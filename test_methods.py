# -*-  coding: utf-8 -*-
"""
Mass data storage test case for Riak
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from thread import start_new_thread
import time

import sys
from gevent import monkey
from py2map import Dictomap

monkey.patch_all()

import threading
import uuid
from schemas import make_student_data
import riak


DEFAULT_BUCKET_NAME = 'my_bucket'


class RiakTest(object):
    def __init__(self, workers=1, total_records=100):

        self.bucket_name = None
        self.bucket_type = None
        self.workers = workers
        self.record_per_worker = total_records / self.workers
        self.total_records = total_records
        self.student = make_student_data()
        self.client = riak.RiakClient
        self.bucket = riak.RiakBucket


    def setup_client(self, host, port, typ='pbc'):
        self.client = riak.RiakClient(protocol='pbc', host=host, pb_port=port) \
            if typ == 'pbc' else \
            riak.RiakClient(protocol='http', host=host, http_port=port)


    def set_bucket(self, bucket_type, bucket_name):
        self.bucket_type = bucket_type
        self.bucket_name = bucket_name
        self.bucket = self.client.bucket_type(self.bucket_type).bucket(self.bucket_name)

    def save_students(self):
        student = make_student_data()
        self.bucket.new(student['identity_information']['tc_no'], student).store()

    def save_same_student(self):
        self.bucket.new(str(uuid.uuid1()), self.student).store()

    def save_map_student(self):
        student = make_student_data()
        m_student = Dictomap(self.bucket, student, student['identity_information']['tc_no'])
        m_student.map.store()

    def save_same_map_student(self):
        m_student = Dictomap(self.bucket, self.student, str(uuid.uuid1()))
        m_student.map.store()

    def range_save(self):
        for i in range(self.record_per_worker):
            self.test_method()

    def run(self):
        threads = [threading.Thread(target=self.range_save, args=()) for i in range(self.workers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()


    def count_keys(self):
        return sum([len(key_list) for key_list in self.bucket.stream_keys()])

    def start_test(self, method):
        self.test_method = getattr(self, method)
        existing_record_count = self.count_keys()
        start_time = time.time()
        self.run()
        end_time = time.time()
        elapsed_time = round(end_time - start_time, 1)
        report = {'elapsed': elapsed_time, 'new_count': self.count_keys(),
                  'workers': self.workers, 'record_per_worker': self.record_per_worker,
                  'test_method': method, 'sys_info': sys.version}
        report['total_new'] = report['new_count'] - existing_record_count
        report['per_sec'] = round(report['total_new'] / elapsed_time)
        report['per_sec_per_worker'] = round(report['total_new'] / elapsed_time / self.workers)
        print("\n\n:::REPORT:::::::::::::::::::::\n\n"
              "{sys_info}\n\n"
              "{test_method} method running with the following configurations:\n\n"
              "{total_new} records saved in {elapsed} secs.\n"
              "Total record count: {new_count}\n"
              "{workers} worker run with {record_per_worker} jobs for each.\n"
              "{per_sec} records stored per sec.\n"
              "{per_sec_per_worker} record stored by each worker per second\n\n"
              ":::::::::::::::::::::::::::::::\n\n".format(**report))


if __name__ == '__main__':
    rt = RiakTest(workers=5, total_records=1000)
    rt.setup_client(host='10.91.5.26', port=8087, typ='pbc')  # z5 public ip: 62.210.245.199 http port: 8098
    # rt.set_bucket('default', 'student')
    # rt.start_test(method='save_students')
    rt.set_bucket('maps', 'student')
    # rt.start_test(method='save_map_student')
    rt.start_test(method='save_same_map_student')
    # rt.start_test(method='save_same_student')