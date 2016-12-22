# -*-  coding: utf-8 -*-
"""
data models for tests
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from pyoko import Model, ListNode, field
from pyoko.model import LinkProxy


class Permission(Model):
    name = field.String('Name', index=False)
    codename = field.String('Codename', index=False)

    def pre_creation(self):
        self.key = self.codename

    def __unicode__(self):
        return "Perm %s" % self.codename
    #
    # class abstract_role_set(ListNode):
    #     abstract_role = AbstractRole()


class AbstractRole(Model):
    name = field.String("Name")

    class Permissions(ListNode):
        permission = Permission(reverse_name='perms')


class User(Model):
    name = field.String('Full Name')
    supervisor = LinkProxy('User', verbose_name='Supervisor', reverse_name='workers')
    test_supervisor = LinkProxy('User',reverse_link=True)

    def __unicode__(self):
        return "User %s" % self.name


class Role(Model):
    usr = User(verbose_name='Kul', reverse_name='roller')
    teammate = LinkProxy('User', verbose_name="Teammate", reverse_name="team")
    abstract_role = AbstractRole()
    name = field.String("Name")
    active = field.Boolean("Is Active", index=True)
    start = field.Date("Start Date", index=False)
    end = field.Date("End Date", index=False)

    def __unicode__(self):
        return "%s role" % self.name


class Employee(Model):
    usr = User(one_to_one=True)
    eid = field.String("Employee ID")
    pre_save_counter = 0
    post_save_counter = 0
    post_creation_counter = 0

    def __unicode__(self):
        return "Employee ID #%s" % self.eid

    def post_creation(self):
        self.post_creation_counter += 1

    def pre_save(self):
        self.pre_save_counter += 1

    def post_save(self):
        self.post_save_counter += 1

    def pre_delete(self):
        self.pre_save_counter -= 1

    def post_delete(self):
        self.post_save_counter -= 1


TIMES = ((1, 'One'), (2, 'Two'), (3, 'Three'))


class TimeTable(Model):
    lecture = field.String("Lecture")
    week_day = field.Integer("Week day")
    hours = field.Integer("Hours", default=1, choices=TIMES)
    adate = field.Date()
    bdate = field.Date()
    # added for testing, it's not logical
    self_table = LinkProxy('TimeTable')
    first_role = Role('First Role',reverse_link = True)
    second_role = Role('Second Role',reverse_link = True)


    def __unicode__(self):
        return 'TimeTable for %s' % self.lecture

    # added for testing, it's not logical
    class Employee(ListNode):
        employee = Employee()

class Scholar(Model):
    name = field.String("Name")

    def __unicode__(self):
        return 'Scholar named %s' % self.name

    class TimeTables(ListNode):
        timetable = TimeTable(reverse_link = True)
        test_timetable= TimeTable(reverse_link=True)
        time_test = TimeTable(reverse_link=True)
        confirmed = field.Boolean("Is confirmed")

