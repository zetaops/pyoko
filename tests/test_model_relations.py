# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from pprint import pprint
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
    def prepare_testbed(cls):
        if not cls.cleaned_up:
            for model in [User, Employee, Scholar, TimeTable, Permission,
                          AbstractRole, Role]:
                model.objects._clear_bucket()
            sleep(2)
            cls.cleaned_up = True

    # def test_one_to_one_simple_benchmarked(self, benchmark):
    #     benchmark(self.test_one_to_one_simple)

    def test_one_to_one_simple(self):
        self.prepare_testbed()
        user = User(name='Joe').save()
        employee = Employee(eid='E1', usr=user).save()
        # need to wait a sec because we will query solr in the
        # _save_backlinked_models of User object
        sleep(1)
        employee_from_db = Employee.objects.get(employee.key)
        assert employee_from_db.usr.name == user.name
        user_from_db = User.objects.get(user.key)


        user_from_db.name = 'Joen'
        user_from_db.save()
        employee_from_db = Employee.objects.get(employee.key)
        assert employee_from_db.usr.name == user_from_db.name

    def test_many_to_many_simple(self):
        self.prepare_testbed()
        scholar = Scholar(name='Munu')
        tt1 = TimeTable(lecture='rock101', week_day=2, hours=2).save()
        tt2 = TimeTable(lecture='math101', week_day=4, hours=4).save()
        scholar.TimeTables(timetable=tt1, confirmed=True)
        scholar.TimeTables(timetable=tt2, confirmed=False)
        scholar.save()
        db_scholar = Scholar.objects.get(scholar.key)
        db_tt1 = db_scholar.TimeTables[0].timetable
        db_tt2 = db_scholar.TimeTables[1].timetable
        assert db_tt2.lecture != db_tt1.lecture
        assert tt1.lecture == db_tt1.lecture

    def test_many_to_many_to_one(self):
        self.prepare_testbed()
        perm = Permission(name="Can see employee data",
                          codename="employee.all").save()
        abs_role = AbstractRole(name="Employee Manager")
        abs_role.Permissions(permission=perm)
        abs_role.save()
        user = User(name='Adams').save()
        role = Role(usr=user, abstract_role=abs_role, active=True).save()
        user_db = User.objects.get(user.key)
        assert role.key == user_db.role_set[0].role.key
