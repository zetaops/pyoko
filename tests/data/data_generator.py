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

# from gevent import monkey

# from pyoko.base import SolRiakcess
from pyoko.field import DATE_FORMAT
from pyoko.lib.py2map import Dictomap


# monkey.patch_all()


from faker import Faker
from tests.models import Student

f = Faker(locale='tr_TR')

def random_student():
    first_name = f.first_name()
    last_name = f.last_name()
    s = Student()
    s.number = f.random_int(10000000000, 19999999999)
    s.deleted = f.random_element(False, False, False, False, False, False, True)
    s.archived = f.random_element(False, False, False, False, False, False, True)
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
        self.record_per_worker = total_records / self.workers
        self.total_records = total_records
        self.student = random_student()


    def save_student(self):
        random_student().save()


    def range_save(self):
        for i in range(self.record_per_worker):
            self.test_method()

    def run_threads(self):
        threads = [threading.Thread(target=self.range_save, args=())
                   for i in range(self.workers)]
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
        existing_record_count = Student.objects._count_bucket()
        elapsed_time = self._timeit(self.run_threads)
        report = {'elapsed': elapsed_time,
                  'new_count': Student.objects._count_bucket(),
                  'workers': self.workers,
                  'record_per_worker': self.record_per_worker,
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
    rt = GenerateRandomData(workers=2, total_records=1000)
    rt.start_process(method='save_student')
