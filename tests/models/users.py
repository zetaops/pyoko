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

    #
    # class abstract_role_set(ListNode):
    #     abstract_role = AbstractRole()


class AbstractRole(Model):
    name = field.String("Name")

    class Permissions(ListNode):
        permission = Permission()


class User(Model):
    name = field.String('Full Name', index=True)
    supervisor = LinkProxy('User', verbose_name='Supervisor', reverse_name='workers')
    def __unicode__(self):
        return "User %s" % self.name




class Role(Model):
    usr = User(verbose_name='Kul', reverse_name='roller')
    teammate = LinkProxy('User', verbose_name="Teammate", reverse_name="team")
    abstract_role = AbstractRole()
    name = field.String("Name")
    active = field.Boolean("Is Active", index=False)
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



class TimeTable(Model):
    lecture = field.String("Lecture", index=True)
    week_day = field.Integer("Week day", index=True)
    hours = field.Integer("Hours", index=True)

    def __unicode__(self):
        return 'TimeTable for %s' % self.lecture


class Scholar(Model):
    name = field.String("Name", index=True)

    def __unicode__(self):
        return 'Scholar named %s' % self.name

    class TimeTables(ListNode):
        timetable = TimeTable()
        confirmed = field.Boolean("Is confirmed", index=True)


