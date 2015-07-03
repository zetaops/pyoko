# -*-  coding: utf-8 -*-
"""
data models for tests
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

from pyoko.model import Model, ListNode, field

class User(Model):
    name = field.String('Full Name', index=True)

# class Unit(Model):
#     parent = field.Link("Unit")
#     name = field.String()
#     type = field.String()

# class Location(Model):
#     unit = Unit()
#     name = field.String()


class Employee(Model):
    usr = User(one_to_one=True)
    role = field.String("Role", index=True)

class TimeTable(Model):
    lecture = field.String("Lecture", index=True)
    week_day = field.Integer("Week day", index=True)
    hours = field.Integer("Hours", index=True)


class Scholar(Model):
    name = field.String("Name", index=True)

    class TimeTables(ListNode):
        timetable = TimeTable()
        confirmed = field.Boolean("Is confirmed", index=True)
