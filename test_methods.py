# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from thread import start_new_thread
import time

# from connection import client
import threading
from schemas import make_student_data
import riak

DEFAULT_BUCKET_NAME = 'my_bucket'


class RiakTest(object):
    def __init__(self, test_method, concurrency=1, bucket_name=None):

        self.BUCKET_NAME = bucket_name or DEFAULT_BUCKET_NAME
        self.concurrency = concurrency
        self.save_method = getattr(self, test_method)
        self.bucket = self.get_bucket()

    def get_bucket(self):
        return riak.RiakClient(protocol='pbc', host='62.210.245.199', pb_port='8087').bucket(self.BUCKET_NAME)

    def save_students(self, bucket):
        student = make_student_data()
        std_obj = bucket.new(student['identity_information']['tc_no'], student)
        std_obj.store()

    def range_save(self):
        bucket = self.get_bucket()
        for i in range(100):
            self.save_students(bucket)
            # self.save_students()

    def run(self):
        threads = [threading.Thread(target=self.range_save, args=()) for i in range(self.concurrency)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    def count_keys(self):
        return sum([len(x) for x in self.bucket.stream_keys()])

    def start_test(self):
        existing_record_count = self.count_keys()
        start_time = time.time()
        self.run()
        end_time = time.time()
        new_record_count = self.count_keys()
        total_new_record_count = new_record_count - existing_record_count
        elapsed_time = round(end_time - start_time, 1)
        print("%s records saved in %s secs." % (total_new_record_count, elapsed_time))


if __name__ == '__main__':
    rt = RiakTest('save_students', concurrency=2, bucket_name='student')
    rt.start_test()