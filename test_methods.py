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
monkey.patch_all()

import threading
import uuid
from schemas import make_student_data
import riak


DEFAULT_BUCKET_NAME = 'my_bucket'


class RiakTest(object):
    def __init__(self, workers=1, bucket_name=None, total_records=100):

        self.BUCKET_NAME = bucket_name or DEFAULT_BUCKET_NAME
        self.workers = workers

        self.record_per_worker = total_records / self.workers
        self.total_records = total_records
        self.student = make_student_data()
        self.client = riak.RiakClient


    def setup_client(self, host, port, typ='pbc'):
        self.client = riak.RiakClient(protocol='pbc', host=host, pb_port=port) \
            if typ == 'pbc' else \
            riak.RiakClient(protocol='http', host=host, http_port=port)

    def save_students(self):
        # sleep(0.1)
        student = make_student_data()
        # sleep(0.1)
        self.client.bucket(self.BUCKET_NAME).new(student['identity_information']['tc_no'], student).store()

    def save_same_student(self):
        self.client.bucket(self.BUCKET_NAME).new(str(uuid.uuid1()), self.student).store()


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
        return sum([len(key_list) for key_list in self.client.bucket(self.BUCKET_NAME).stream_keys()])

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
    rt = RiakTest(workers=5, bucket_name='student', total_records=10000)
    rt.setup_client(host='10.91.5.26', port=8087, typ='pbc')  # z5 public ip: 62.210.245.199 http port: 8098
    rt.start_test(method='save_students')
    # rt.start_test(method='save_same_student')