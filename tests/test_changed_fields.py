# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from datetime import datetime
from .models import Student, TimeTable, Uniques, Role, User


class TestCase:
    def test_changed_fields(self):

        # String, Date and ListNode test
        s = Student.objects.all()[0]
        name = '%s_test' % s.name
        s.name = name
        s.join_date = datetime.now().date()
        s.Lectures(name='test_string')
        assert s.is_changed('name') == s.is_changed('join_date') == s.is_changed('lectures') == True
        assert 'name' and 'join_date' and 'lectures' in s.changed_fields()
        assert 'pno' and 'number' not in s.changed_fields()

        # Integer test
        t = TimeTable.objects.all()[0]
        week_day = t.week_day + 1
        t.week_day = week_day
        assert t.is_changed('week_day') == True
        assert 'week_day' in t.changed_fields()
        assert 'lecture' and 'hours' not in t.changed_fields()

        # Datetime test
        u = Uniques.objects.all()[0]
        assert u.join_date != datetime.now()
        u.join_date = datetime.now()
        assert u.is_changed('join_date') == True
        assert 'join_date' in u.changed_fields()
        assert 'rel_id' and 'id' not in u.changed_fields()

        # Boolean and Link test
        r = Role.objects.all()[0]
        user = ''
        for user in User.objects.all():
            if user != r.usr:
                break
        bool = r.active
        r.active = bool
        assert r.is_changed('active') == False
        assert 'active' not in r.changed_fields()
        r.active = not bool
        r.usr = user
        assert r.is_changed('usr_id') == r.is_changed('active') == True
        assert 'active' and 'usr_id' in r.changed_fields()
        r.active = bool
