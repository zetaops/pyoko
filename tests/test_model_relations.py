# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from pprint import pprint, pformat
from time import sleep, time

from pyoko.exceptions import ObjectDoesNotExist
from pyoko.manage import FlushDB
from .models import *
import pytest


class TestCase:
    """
    tests for many to one, one to one functionalities of pyoko
    sleep() s are required to give enough time to yokozuna for update solr index
    """
    cleaned_up = False
    index_checked = False

    @classmethod
    def prepare_testbed(cls, force=False):
        if force or not cls.cleaned_up:
            FlushDB(model=('User,Employee,Scholar,TimeTable,'
                           'Permission,AbstractRole,Role')
                    ).run()
            cls.cleaned_up = True

    # def test_one_to_one_simple_benchmarked(self, benchmark):
    #     benchmark(self.test_one_to_one_simple)

    def test_one_to_one_simple(self):
        self.prepare_testbed()
        user = User(name='Joe').save()
        print(user.key)
        employee = Employee(eid='E1', usr=user)
        employee.save()
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
        assert user_from_db.employee.eid == employee.eid

    @pytest.mark.second
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
        assert db_tt1.scholar_time_tables_timetable_set[0].scholar.name == db_scholar.name
        assert db_sc_tt2.lecture != db_sc_tt1.lecture
        assert tt1.lecture == db_tt1.lecture

    @pytest.mark.second
    def test_many_to_many_to_one(self):
        self.prepare_testbed()
        perm = Permission(name="Can see employee data",
                          codename="employee.all").save()
        abs_role = AbstractRole(name="Employee Manager")
        abs_role.Permissions(permission=perm)
        abs_role.save()
        db_perm = Permission.objects.get(perm.key)
        assert len(db_perm.abstract_role_permissions_permission_set) == 1
        user = User(name='Adams')
        user.save()
        role = Role(abstract_role=abs_role, active=True)
        # role = Role(usr=user, abstract_role=abs_role, active=True)
        role.usr = user
        role.save()
        user_db = User.objects.get(user.key)
        assert role.key == user_db.role_usr_set[0].role.key
        role_node = user_db.role_usr_set[0]
        db_user_role_abs_role = role_node.role.abstract_role
        assert abs_role.name == db_user_role_abs_role.name
        db_abs_role = AbstractRole.objects.get(abs_role.key)
        # this works:
        assert perm.codename == db_abs_role.Permissions[0].permission.codename
        # but this would fail, cause denormalization doesn't reach this far, yet!
        # assert perm.codename == db_user_role_abs_role.Permissions[0].permission.codename

    @pytest.mark.second
    def test_missing_relations_simple(self):
        self.prepare_testbed()
        u = User(name="Foo").save()
        r = Role(usr=u, name="Foo Frighters").save()
        assert Role.objects.get(r.key).usr.name == u.name

    @pytest.mark.second
    def test_missing_link(self):
        """
        Tries to create a Role object with nonexistent user
        and expects ObjectDoesNotExist error
        :return:
        """
        self.prepare_testbed()
        with pytest.raises(ObjectDoesNotExist):
            Role(usr_id='nonexistent_user_key', name="Foo Frighters").save()

    @pytest.mark.second
    def test_lazy_links(self):
        self.prepare_testbed()
        u = User(name="Foo").save()
        mate = User(name="Mate").save()
        r = Role(usr=u, teammate=mate, name="Foo Fighters").save()
        db_role = Role.objects.get(r.key)
        assert db_role.teammate.name == mate.name
        assert db_role.usr.name == u.name

    @pytest.mark.second
    def test_self_reference(self):
        self.prepare_testbed()
        ceo = User(name="CEO").save()
        mate1 = User(name="Mate", supervisor=ceo).blocking_save()
        mate2 = User(name="Mate2", supervisor=ceo).blocking_save()
        ceo.reload()
        assert mate1 in ceo.user_supervisor_set
        assert mate2 in ceo.user_supervisor_set
        assert len(ceo.user_supervisor_set) == 2

        assert ceo not in mate1.user_supervisor_set
        assert ceo not in mate2.user_supervisor_set
        assert len(mate1.user_supervisor_set) == 0
        assert len(mate2.user_supervisor_set) == 0


    def test_delete_rel_many_to_one(self, force=True):
        self.prepare_testbed()
        can_sleep = Permission(name="can sleep", codename='can_sleep').save()
        can_feat = Permission(name="can feat", codename='can_feat').save()
        arole = AbstractRole(name="arole")
        arole.Permissions(permission=can_sleep)
        arole.Permissions(permission=can_feat)
        arole.blocking_save()
        can_feat.blocking_delete()
        arole.reload()
        assert can_feat not in arole.Permissions
        assert can_sleep in arole.Permissions

    @pytest.mark.first
    def test_delete_rel_many_to_many(self, force=True):
        self.prepare_testbed()
        can_eat = Permission(name="can eat", codename='can_eat').blocking_save()
        arole = AbstractRole(key="arole").save()
        brole = AbstractRole(key="brole").save()
        arole.Permissions(permission=can_eat)
        brole.Permissions(permission=can_eat)
        arole.blocking_save()
        brole.blocking_save()
        del arole.Permissions[can_eat]
        arole.save()
        can_eat.reload()
        assert arole not in can_eat.abstract_role_permissions_permission_set
        assert brole in can_eat.abstract_role_permissions_permission_set

    def test_delete_rel_one_to_many(self):
        self.prepare_testbed()
        user = User(name='foobar').save()
        role = Role(usr=user).blocking_save()
        user.blocking_delete()
        role.reload()
        assert not role.usr.exist

    def test_set_listnode_rel_by_id(self):
        p = Permission(code='can_see').save()
        ar1 = AbstractRole()
        ar2 = AbstractRole()
        ar1.Permissions(permission=p)
        ar1.blocking_save()
        ar2.Permissions(permission_id=p.key)
        ar2.blocking_save()
        ar1.reload()
        ar2.reload()
        assert ar1.Permissions[0].permission == ar2.Permissions[0].permission

    def test_set_rel_by_id(self):
        u = User().save()
        r1 = Role()
        r1.usr_id = u.key
        r1.blocking_save()
        r1.reload()
        r2 = Role()
        r2.usr = u
        r2.blocking_save()
        r2.reload()
        assert r1.usr == r2.usr


    def test_reverse_link(self):
        self.prepare_testbed()

        # REVERSE LINK DEFAULT FALSE

        # Link from Role model to AbstractRole
        assert 'role_abstract_role' not in AbstractRole().clean_value()
        # One to one relationship should be created
        assert 'employee_id' in User().clean_value()
        assert 'usr_id' in Employee().clean_value()
        # Link set shouldn't be created in one to one relationships.
        assert 'employee_usr_set' not in User().clean_value()
        # Link from TimeTable model Employee listnode employee field to Employee model
        assert 'time_table_employee_employee_set' not in Employee().clean_value()
        # Link from TimeTable to itself
        # Field name should be created
        assert 'self_table_id' in TimeTable().clean_value()
        # Link set should not be created
        assert 'time_table_self_table_set' not in TimeTable().clean_value()

        # REVERSE LINK TRUE

        # Link from model, two links from model to same model

        # Link from TimeTable model first_role field to Role model
        assert 'time_table_first_role_set' in Role().clean_value()
        # Link from TimeTable model second_role field to Role model
        assert 'time_table_second_role_set' in Role().clean_value()

        arole = Role()
        brole = Role()
        arole.save()
        brole.save()

        atime = TimeTable(first_role = arole)
        atime.save()
        btime = TimeTable(second_role = brole)
        btime.save()

        assert len(arole.time_table_first_role_set) == 1
        assert len(arole.time_table_second_role_set) == 0
        assert arole.time_table_first_role_set[0].time_table.key == atime.key

        assert len(brole.time_table_second_role_set) == 1
        assert len(brole.time_table_first_role_set) == 0
        assert brole.time_table_second_role_set[0].time_table.key == btime.key

        # Link from Listnode to model

        # Link from AbstractRole model Permissions listnode permission field
        assert 'abstract_role_permissions_permission_set' in Permission().clean_value()

        p = Permission()
        p.save()
        a = AbstractRole()
        a.Permissions(permission = p)
        a.save()
        assert len(a.Permissions) == 1
        assert a.Permissions[0].permission.key == p.key
        assert p.abstract_role_permissions_permission_set[0].abstract_role.key == a.key

        # Two links from Listnode to same model

        # Link from Student model Lectures listnode role field
        assert 'scholar_time_tables_timetable_set' in TimeTable().clean_value()
        # Link from Student model Lectures listnode test_role field
        assert 'scholar_time_tables_test_timetable_set' in TimeTable().clean_value()

        s= Scholar(name = 'test_scholar')
        t1 = TimeTable()
        t2 = TimeTable()
        t1.save()
        t2.save()
        s.TimeTables(timetable = t1)
        s.TimeTables(test_timetable=t2)
        s.save()
        assert len(s.TimeTables) == 2
        assert len(t1.scholar_time_tables_timetable_set) == 1
        assert len(t1.scholar_time_tables_test_timetable_set) == 0
        assert len(t1.scholar_time_tables_time_test_set) == 0

        assert len(t2.scholar_time_tables_timetable_set) == 0
        assert len(t2.scholar_time_tables_test_timetable_set) == 1
        assert len(t2.scholar_time_tables_time_test_set) == 0

        assert t2.scholar_time_tables_test_timetable_set[0].scholar.name ==s.name
        assert t1.scholar_time_tables_timetable_set[0].scholar.name ==s.name

        s = Scholar(name='second_test')
        s.save()
        s.TimeTables(timetable=t1)
        s.TimeTables(time_test=t1)
        s.save()
        assert len(s.TimeTables) == 2
        assert len(t1.scholar_time_tables_timetable_set) == 2
        assert len(t1.scholar_time_tables_test_timetable_set) == 0
        assert len(t1.scholar_time_tables_time_test_set) == 1

        assert t1.scholar_time_tables_time_test_set[0].scholar.name == s.name

        # Two self reference

        assert 'supervisor_id' in User().clean_value()
        assert 'test_supervisor_id' in User().clean_value()
        assert 'user_supervisor_set' in User().clean_value()
        assert 'user_test_supervisor_set' in User().clean_value()

        u = User(name = 'test_name')
        uu = User(name = 'test_second_name')
        uu.save()
        u.supervisor = uu
        u.save()

        assert u.supervisor == uu
        assert u.test_supervisor.key == None
        assert len(uu.user_supervisor_set) == 1
        assert len(uu.user_test_supervisor_set) == 0
        assert uu.user_supervisor_set[0].user.name == u.name

        uu.test_supervisor = u
        uu.save()

        assert uu.test_supervisor == u
        assert uu.supervisor.key == None
        assert len(u.user_test_supervisor_set) == 1
        assert len(u.user_supervisor_set) == 0
        assert u.user_test_supervisor_set[0].user.name == uu.name



    def test_same_links_different_listnode(self):
        """
        Same links at different listnodes under same class shouldn't affect each other.
        They should be independent.

        Test example architecture:

        class Student(Model):

            class Lecturer(ListNode):
                role = Role()

            class Lectures(ListNode):
                role = Role()

        """
        # First role is taken.
        first_role = Role()
        # Second role is taken.
        second_role = Role()
        # First and second roles are saved.
        first_role.save()
        second_role.save()
        # Student instance is creaeted.
        student = Student()
        # First and second roles' student sets are controlled.
        assert len(first_role.student_lecturer_role_set) == 0
        assert len(first_role.student_lectures_role_set) == 0
        assert len(second_role.student_lecturer_role_set) == 0
        assert len(second_role.student_lectures_role_set) == 0
        # Student's Lecturer list node's role field is assigned to first_role.
        student.Lecturer(role=first_role)
        # Student instance is saved.
        student.save()
        # Student's Lecturer list increases one, it is controlled.
        assert len(student.Lecturer) == 1
        # Student's Lectures list remains same, it is controlled.
        assert len(student.Lectures) == 0
        # Student's Lecturer data's role info is controlled.
        assert student.Lecturer[0].role == first_role
        # First role's student set number should increase one.
        assert len(first_role.student_lecturer_role_set) == 1
        # First role's student set's student object's data is controlled.
        # Role info is controlled whether it is true or not.
        assert first_role.student_lecturer_role_set[0].student.clean_value()['lecturer'][0]['role_id'] == first_role.key
        assert len(first_role.student_lectures_role_set) == 0

        # Student's Lectures list node's role field is assigned to first_role.
        student.Lectures(role=first_role)
        # Student instance is saved.
        student.save()

        # Lecturer and Lectures listnodes' number should be 1.
        assert len(student.Lectures) == 1
        assert len(student.Lecturer) == 1
        # Both's role data should be first_role
        assert student.Lecturer[0].role == first_role
        assert student.Lectures[0].role == first_role
        # First role student set's number should remain same.
        assert len(first_role.student_lecturer_role_set) == 1
        # First role's student set's student object's data is controlled.
        # Role info is controlled whether it is true or not.
        assert first_role.student_lecturer_role_set[0].student.clean_value()['lecturer'][0]['role_id'] == first_role.key
        assert first_role.student_lectures_role_set[0].student.clean_value()['lecturer'][0]['role_id'] == first_role.key

        # Student's Lecturer list node's role field is changed from first_role to second_role.
        student.Lecturer[0].role = second_role
        # Student instance is saved.
        student.save()

        # Student's Lecturer list number should be 1.
        assert len(student.Lecturer) == 1
        # Student's Lectures list number should be 1.
        assert len(student.Lectures) == 1
        # Changes are controlled.
        assert student.Lecturer[0].role == second_role
        assert student.Lectures[0].role == first_role
        # # Second role's student set number should increase one.
        # assert len(second_role.student_set) == 1
        # # Second role's student set's student object's data is controlled.
        # assert second_role.student_set[0].student.clean_value()['lecturer'][0]['role_id'] == second_role.key