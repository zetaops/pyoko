# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from .models import TimeTable


class TestCase():
    def test_choices_display(self):
        t1 = TimeTable()

        assert t1.hours == 1
        assert t1.get_hours_display() == 'One'

        t2 = TimeTable()
        t2.hours = 2
        assert t2.get_hours_display() == 'Two'

        t3 = TimeTable(hours=3)
        assert t3.get_hours_display() == 'Three'
