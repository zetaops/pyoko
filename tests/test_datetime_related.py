# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from time import sleep

from pyoko.manage import FlushDB
from tests.models.date_models import *


class TestCase:
    """
    tests for format parameter of date/datetime fields
    """
    cleaned_up = False
    index_checked = False

    @classmethod
    def prepare_testbed(cls):
        if not cls.cleaned_up:
            FlushDB(model='DateModel').run()
            cls.cleaned_up = True


    def test_date_formatting(self):
        self.prepare_testbed()
        dm = DateModel(name='foo')
        ln = dm.LNodeWithDate()
        ln.date_with_format = '20.01.2001'
        ln.name = 'foo'
        dm.save()
        from_db = DateModel.objects.get(dm.key)
        assert from_db.LNodeWithDate[0].date_with_format == ln.date_with_format



