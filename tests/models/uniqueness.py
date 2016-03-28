# -*-  coding: utf-8 -*-
"""
test model for unique and unique_together features
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from pyoko import Model, ListNode, field, Node


class Uniques(Model):
    id = field.String()
    foo_id = field.String()
    name = field.String()
    username = field.String(unique=True)
    join_date = field.Date(unique=True, default='now')

    class Meta:
        unique_together = [('id', 'foo_id')]

