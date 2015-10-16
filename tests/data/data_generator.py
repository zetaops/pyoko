# -*-  coding: utf-8 -*-
"""
Mass data storage test case for Riak
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import sys
import time
import threading
import uuid
import riak
import redis

redis_client = redis.Redis('ulakbus-load-balancer-02.zetaops.local', '6379')

# riak_host = ''
riak_host = ''

riak_client = riak.RiakClient(protocol='pbc', host=riak_host, pb_port='8087')
# riak_client = riak.RiakClient(protocol='http', host=riak_host, http_port='8098')

# FOR localhost
# redis_client = redis.Redis()
# riak_client = riak.RiakClient(protocol='pbc', riak_host='localhost', pb_port='8087')


m1_bucket = riak_client.bucket_type("memory_mult").bucket("m4")
print(m1_bucket.get_properties())
# m1_bucket = riak_client.bucket("m1")

# from gevent import monkey
# monkey.patch_all()





# from pyoko.base import SolRiakcess
# from pyoko.field import DATE_FORMAT
# from pyoko.lib.py2map import Dictomap




# from faker import Faker
# from tests.models import Student
#
# f = Faker(locale='tr_TR')

def random_student():
    first_name = f.first_name()
    last_name = f.last_name()
    s = Student()
    s.number = f.random_int(10000000000, 19999999999)
    s.deleted = f.random_element(False, False, False, False, False, False, True)
    s.bio = '\n'.join(f.paragraphs())
    s.name = first_name
    s.surname = last_name
    s.pno = str(f.random_int(10000000000, 19999999999))
    s.join_date = f.date_time_between('-2000d', '-180d').strftime(DATE_FORMAT)

    ai = s.AuthInfo()
    ai.email = f.email()
    ai.password = f.sha256()
    ai.username = f.simple_profile()['username']
    return s


class GenerateRandomData(object):
    def __init__(self, workers=1, total_records=100):
        super(GenerateRandomData, self).__init__()
        self.workers = workers
        self.record_per_worker = int(total_records / self.workers)
        self.total_records = total_records
        self.mass_data = []
        # self.student = random_student()

    def prepare_read_from_riak_m1(self):
        self._get_rand_key = self._get_rand_key_with_store
        for i in range(self.total_records):
            self.save_to_riak_m1()


    def prepare_read_from_redis_m1(self):
        self._get_rand_key = self._get_rand_key_with_store
        for i in range(self.total_records):
            self.save_to_redis_m1()

    def save_student(self):
        random_student().save()


    def _get_rand_key_with_store(self):
        key = uuid.uuid4().hex
        self.mass_data.append(key)
        return key

    def _get_rand_key(self):
        return uuid.uuid4().hex

    def save_to_riak_m1(self):
        m1_bucket.new(self._get_rand_key(), "askajdkasd", content_type="text/plain").store()

    def save_to_redis_m1(self):
        redis_client.set(self._get_rand_key(), "askajdkasd")

    def read_from_riak_m1(self, key):
        m1_bucket.get(key, content_type="text/plain")

    def read_from_redis_m1(self, key):
        redis_client.get(key)

    def range_run(self, thread_id):
        if self.mass_data:
            start =  self.record_per_worker * (thread_id -1)
            end = self.record_per_worker * thread_id
            data = self.mass_data[start:end]
            for i in range(self.record_per_worker):
                self.test_method(data[i])
        else:
            for i in range(self.record_per_worker):
                self.test_method()

    def run_threads(self):
        threads = []
        for i in range(self.workers):
            threads.append(threading.Thread(target=self.range_run, args=(i,)))
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    @staticmethod
    def _timeit(method, round_by=1):
        start_time = time.time()
        method()
        end_time = time.time()
        return round(end_time - start_time, round_by)

    def start_process(self, method):
        self.test_method = getattr(self, method)
        if hasattr(self, "prepare_%s" % method):
            print("Running preparation method")
            getattr(self, "prepare_%s" % method)()
        # existing_record_count = Student.objects._count_bucket()
        elapsed_time = self._timeit(self.run_threads)
        report = {'elapsed': elapsed_time,
                  'new_count': self.total_records,
                  'workers': self.workers,
                  'record_per_worker': self.record_per_worker,
                  'test_method': method, 'sys_info': sys.version}
        report['total_new'] = report['new_count']
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
    rt = GenerateRandomData(workers=3, total_records=10000)
    # rt.start_process(method='save_to_redis_m1')
    rt.start_process(method='save_to_riak_m1')
