# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from time import sleep

import pytest

from pyoko.exceptions import IntegrityError
from pyoko.manage import FlushDB
from tests.models import Uniques, UniqRelation, OtherUniqRelation


class TestCase():
    cleaned_up = False
    index_checked = False

    @classmethod
    def prepare_testbed(cls, reset=False):
        if (not cls.cleaned_up) or reset:
            FlushDB(model=','.join(('Uniques',))).run()
            sleep(3)
            cls.cleaned_up = True

    def test_unique(self):
        self.prepare_testbed()
        Uniques(id='a', foo_id='b', rel=UniqRelation().save(), username='foo1').save()
        sleep(1)
        with pytest.raises(IntegrityError):
            Uniques(id='a', foo_id='c', username='foo1').save()

    def test_unique_together(self):
        self.prepare_testbed()
        Uniques(id='d', other_rel=OtherUniqRelation().save(), foo_id='e', username='foo2').save()
        sleep(1)
        with pytest.raises(IntegrityError):
            Uniques(id='d', foo_id='e', username='foo3').save()

    def test_unique_together_with_links(self):
        self.prepare_testbed()
        Uniques(id='a', foo_id='ae', username='afoo2').save()
        sleep(1)
        with pytest.raises(IntegrityError):
            Uniques(id='d3', foo_id='e3', username='foo3').save()
