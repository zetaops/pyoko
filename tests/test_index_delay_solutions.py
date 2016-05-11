# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import time

from pyoko.manage import FlushDB
from .models import Student
from pyoko.db.adapter.db_riak import BlockSave

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
#
