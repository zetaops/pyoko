# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from pprint import pprint
from time import sleep, time
from tests.models import *


class TestCase:
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
        # _save_back_linked_models of User object
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

        tt1 = TimeTable(lecture='rock101', week_day=2, hours=2).save()
        tt2 = TimeTable(lecture='math101', week_day=4, hours=4).save()
        scholar = Scholar(name='Munu')
        scholar.TimeTables(timetable=tt1, confirmed=True)
        scholar.TimeTables(timetable=tt2, confirmed=False)
        scholar.save()
        db_scholar = Scholar.objects.get(scholar.key)
        db_tt1 = TimeTable.objects.get(tt1.key)
        db_sc_tt2 = db_scholar.TimeTables[1].timetable
        db_sc_tt1 = db_scholar.TimeTables[0].timetable
        assert db_tt1.scholar_set[0].scholar.name == db_scholar.name
        assert db_sc_tt2.lecture != db_sc_tt1.lecture
        assert tt1.lecture == db_tt1.lecture

    def test_many_to_many_to_one(self):
        self.prepare_testbed()
        perm = Permission(name="Can see employee data",
                          codename="employee.all").save()
        abs_role = AbstractRole(name="Employee Manager")
        abs_role.Permissions(permission=perm)
        abs_role.save()
        db_perm = Permission.objects.get(perm.key)
        assert len(db_perm.abstract_role_set) == 1
        user = User(name='Adams')
        user.save()
        role = Role(usr=user, abstract_role=abs_role, active=True)
        role.save()
        user_db = User.objects.get(user.key)
        assert role.key == user_db.roller[0].role.key
        role_node = user_db.roller[0]
        db_user_role_abs_role = role_node.role.abstract_role
        assert abs_role.name == db_user_role_abs_role.name
        db_abs_role = AbstractRole.objects.get(abs_role.key)
        # this works:
        assert perm.codename == db_abs_role.Permissions[0].permission.codename
        # but this would fail, cause denormalization doesn't reach this far, yet!
        # assert perm.codename == db_user_role_abs_role.Permissions[0].permission.codename

    def test_missing_relations_simple(self):
        self.prepare_testbed()
        u = User(name="Foo").save()
        r = Role(usr=u, name="Foo Frighters").save()
        assert Role.objects.get(r.key).usr.name == u.name





















