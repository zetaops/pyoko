# -*-  coding: utf-8 -*-
"""
Mass data storage test case for Riak
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import sys
from gevent import monkey
from connection import client
from lib.db.base import RiakDataAccess
from lib.py2map import Dictomap


monkey.patch_all()

import threading
import uuid
from schemas import make_student_data
import riak
from faker import Faker

fake = Faker(locale='tr_TR')

class GenerateRandomData(RiakDataAccess):
    def __init__(self, riak_client, workers=1, total_records=100):
        super(GenerateRandomData, self).__init__(riak_client)
        self.workers = workers
        self.record_per_worker = total_records / self.workers
        self.total_records = total_records
        self.student = make_student_data()

    def save_student(self):
        student = make_student_data()
        self.bucket.new(student['identity_information']['tc_no_l'], student).store()

    def save_same_student(self):
        self.bucket.new(str(uuid.uuid1()), self.student).store()

    def save_map_student(self):
        student = make_student_data()
        m_student = Dictomap(self.bucket, student, student['identity_information']['tc_no_l'])
        m_student.map.store()

    def save_same_map_student(self):
        m_student = Dictomap(self.bucket, self.student, str(uuid.uuid1()))
        m_student.map.store()

    def save_something(self):
        self.bucket.new(str(uuid.uuid1()),
            {"name_s":fake.name(), "note_i":fake.random_int(1, 100)}
        ).store()


    def range_save(self):
        for i in range(self.record_per_worker):
            self.test_method()

    def run_threads(self):
        threads = [threading.Thread(target=self.range_save, args=()) for i in range(self.workers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    def start_process(self, method):
        self.test_method = getattr(self, method)
        existing_record_count = self.count_keys()
        elapsed_time = self.timeit(self.run_threads)
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
    rt = GenerateRandomData(client, workers=5, total_records=1000)

    # rt.set_bucket('default', 'student')
    # rt.set_bucket('student', 'student2').start_test(method='save_something')

    rt.set_bucket('student', 'student4')
    print("%s records deleted" % rt.delete_all())
    rt.start_process(method='save_student')

    # rt.start_test(method='save_same_student')

    #rt.set_bucket('student_map2', 'test3')

    # rt.start_test(method='save_same_map_student')

