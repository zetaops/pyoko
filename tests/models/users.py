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
    name = field.String('Name')
    codename = field.String('Codename')

    #
    # class abstract_role_set(ListNode):
    #     abstract_role = AbstractRole()


class AbstractRole(Model):
    name = field.String("Name", index=True)

    class Permissions(ListNode):
        permission = Permission()


class User(Model):
    name = field.String('Full Name', index=True)
    def __unicode__(self):
        return "User %s" % self.name

    def __repr__(self):
        return "User_%s" % self.key



class Role(Model):
    usr = User(verbose_name='Kul', reverse_name='roller')
    teammate = LinkProxy('User', verbose_name="Teammate", reverse_name="team")
    abstract_role = AbstractRole()
    name = field.String("Name", index=True)
    active = field.Boolean("Is Active")
    start = field.Date("Start Date")
    end = field.Date("End Date")

    def __unicode__(self):
        return "%s role" % self.name


class Employee(Model):
    usr = User(one_to_one=True)
    eid = field.String("Employee ID", index=True)

    def __unicode__(self):
        return "Employee ID #%s" % self.eid


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
