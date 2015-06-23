# -*-  coding: utf-8 -*-

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

from tests.models import Student

# this file contains whole levels of queries to pyoko.
# todo: add more complex queries

def test_filter():
    student = Student()
    # filter by name, if name not equals filtered names then append to list
    filter_result = [s.name for s in student.objects.filter(name='Jack') if s.name != 'Jack']

    assert len(filter_result) == 0


def test_exclude():
    student = Student()
    # exclude by name, if name equals filtered names then append to list
    exclude_result = [s.name for s in student.objects.exclude(name='Jack') if s.name == 'Jack']

    assert len(exclude_result) == 0