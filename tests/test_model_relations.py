# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from time import sleep
from tests.models import *


class TestModelRelations:
    """
    tests for many to one, one to one functionalities of pyoko
    sleep() s are required to give enough time to yokozuna for update solr index
    """
    cleaned_up = False
    index_checked = False


    @classmethod
    def preprocess(cls):
        if not cls.cleaned_up:
            for model in [User, Employee, Scholar, TimeTable]:
                model.objects._clear_bucket()
            sleep(2)
            cls.cleaned_up = True

    @classmethod
    def prepare_testbed(cls):
        cls.preprocess()

    # def test_one_to_one_simple_benchmarked(self, benchmark):
    #     benchmark(self.test_one_to_one_simple)

    def test_one_to_one_simple(self):
        self.prepare_testbed()
        user = User(name='Joe').save()
        employee = Employee(role='Coder', usr=user).save()
        sleep(1)
        employee_from_db = Employee.objects.filter(role=employee.role).get()

        assert employee_from_db.usr.name == user.name

        user_from_db = User.objects.filter(name='Joe').get()
        user_from_db.name = 'Joen'
        user_from_db.save()
        sleep(1)
        employee_from_db = Employee.objects.filter(role='Coder').get()

        assert employee_from_db.usr.name == user_from_db.name


    def test_many_to_one_simple(self):
        self.prepare_testbed()
        scholar = Scholar(name='Munu')
        tt1 = TimeTable(lecture='rock101', week_day=2, hours=2).save()
        tt2 = TimeTable(lecture='math101', week_day=4, hours=4).save()
        scholar.TimeTables(timetable=tt1, confirmed=True)
        scholar.TimeTables(timetable=tt2, confirmed=False)
        scholar.save()
        sleep(1)
        db_scholar = Scholar.objects.get()
        db_tt1 = db_scholar.TimeTables[0].timetable
        assert tt1.lecture == db_tt1.lecture
