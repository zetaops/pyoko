# -*-  coding: utf-8 -*-
"""
data models for tests
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from pyoko.db.schema_update import SchemaUpdater
from pyoko.model import Model, Node, ListNode
from pyoko import field


class User(Model):
    name = field.String(index=True)

# class Unit(Model):
#     parent = field.Link("Unit")
#     name = field.String()
#     type = field.String()
#
# class Location(Model):
#     unit = field.Link(Unit)
#     name = field.String()


class Employee(Model):
    # unit = field.Link(Unit)
    # user = field.LinkToOne(User, index=True)
    usr = User(index=True, cache_level=1)
    role = field.String(index=True)


