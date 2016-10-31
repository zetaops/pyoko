# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import time

from .models import Student
from pyoko.db.adapter.db_riak import BlockSave, BlockDelete


class TestCase:
    """
    For the sake of DRY and to speedup tests, we're running clear_bucket
    only once at first test, then creating a new object and reusing it.
    """

    def test_block_save(self):
        Student.objects.filter().delete()
        t1 = time.time()
        with BlockSave(Student):
            for i in range(10):
                Student(surname='bar', name='foo_%s' % i).save()
        assert Student.objects.count() == 10
        print("BlockSave took %s" % (time.time() - t1))
        student = Student.objects.get(surname='bar', name='foo_9')
        student.blocking_save(query_dict={"name": "foo_10", "surname": "bar_10"})
        assert student.name == "foo_10"
        assert student.surname == "bar_10"

    def test_block_delete(self):
        Student.objects.filter().delete()
        time.sleep(1)

        with BlockSave(Student):
            for i in range(10):
                    Student(surname='bar', name='foo_%s' % i).save()
        assert Student.objects.count() == 10
        t1 = time.time()
        with BlockDelete(Student):
            for i in range(10):
                Student.objects.get(surname='bar', name='foo_%s' % i).delete()
        assert Student.objects.count() == 0
        print("BlockDelete took %s" % (time.time() - t1))

