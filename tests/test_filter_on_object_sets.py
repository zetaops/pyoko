# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from pprint import pprint, pformat
from time import sleep, time

from .models import *
import random
from pyoko.manage import FlushDB
import time
import datetime


class TestCase:
    """
    tests for query facility for reverse sets.
    """

    @classmethod
    def prepare_testbed(cls):
        FlushDB(model=('TimeTable')).run()

    def test_filter_on_object_sets(self):
        self.prepare_testbed()

        role = Role()
        role.save()

        number_list = range(20)
        random.shuffle(number_list)

        for number in number_list:
            t = TimeTable(first_role=role, hours=number)
            t.lecture = "meow" if number % 5 == 0 else "heow" if number % 9 == 0 else "leon"
            t.adate = datetime.date(1987, 12, 26) if number % 5 == 0 else datetime.date(1989, 11,
                                                                                        22)
            t.save()

        assert len(role.time_table_first_role_set) == 20

        time.sleep(1)
        assert role.time_table_first_role_set.objects.filter(hours__gt=11,
                                                             hours__lt=17).count() == 5
        assert role.time_table_first_role_set.objects.filter(hours__gte=11,
                                                             hours__lte=17).count() == 7
        assert role.time_table_first_role_set.objects.filter(hours__gte=11,
                                                             hours__lt=17).count() == 6
        assert role.time_table_first_role_set.objects.filter(hours__gt=11,
                                                             hours__lte=17).count() == 6

        assert role.time_table_first_role_set.objects.filter(lecture__startswith='me').count() == 4
        assert role.time_table_first_role_set.objects.filter(lecture__startswith='he').count() == 2
        assert role.time_table_first_role_set.objects.filter(lecture__startswith='me',
                                                             lecture__endswith='wo').count() == 0

        assert role.time_table_first_role_set.objects.filter(lecture__endswith='on').count() == 14

        assert role.time_table_first_role_set.objects.filter(lecture__contains='eo').count() == 20
        assert role.time_table_first_role_set.objects.filter(lecture__contains='h').count() == 2

        assert role.time_table_first_role_set.objects.filter(
            adate=datetime.date(1987, 12, 26)).count() == 4

        assert role.time_table_first_role_set.objects.filter(hours=7, lecture='leon').count() == 1
        assert role.time_table_first_role_set.objects.filter(lecture='heow').count() == 2

        assert role.time_table_first_role_set.objects.filter(
            adate__gt=datetime.date(1988, 12, 26)).count() == 16
        assert role.time_table_first_role_set.objects.filter(adate__gt=datetime.date(1985, 12, 26),
                                                             adate__lt=datetime.date(1988, 11,
                                                                                     22)).count() == 4

        role.blocking_delete()
