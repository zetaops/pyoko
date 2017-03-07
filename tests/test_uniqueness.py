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
from .models import Uniques, UniqRelation, OtherUniqRelation


class TestCase():
    cleaned_up = False
    index_checked = False

    @classmethod
    def prepare_testbed(cls, reset=False):
        if (not cls.cleaned_up) or reset:
            FlushDB(model='Uniques,UniqRelation,OtherUniqRelation', wait_sync=True).run()
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
            Uniques(id='a', foo_id='ae', username='foo3').save()

    def test_unique_update(self):
        self.prepare_testbed()
        Uniques(id='k', foo_id='l', rel=UniqRelation().save(), username='foo4').save()
        sleep(1)
        uni2 = Uniques(id='x', foo_id='y', username='foo5').save()
        sleep(1)
        with pytest.raises(IntegrityError):
            uni2.id = 'k'
            uni2.username = 'foo4'
            uni2.save()

    def test_unique_together_update(self):
        self.prepare_testbed()
        Uniques(id='p', foo_id='pip', username='foo6').save()
        sleep(1)
        uni2 = Uniques(id='p', foo_id='pep', username='foo7').save()
        sleep(1)
        with pytest.raises(IntegrityError):
            uni2.foo_id = 'pip'
            uni2.save()

    def test_unique_together_update_with_links(self):
        self.prepare_testbed()
        rel = UniqRelation().save()
        other_rel = OtherUniqRelation().save()
        Uniques(id='l', rel=rel, other_rel=other_rel, foo_id='lamp', username='foo8').save()
        sleep(1)
        uni2 = Uniques(id='q', rel=UniqRelation().save(), other_rel=OtherUniqRelation().save(),
                       foo_id='qq', username='foo9').save()
        sleep(1)
        with pytest.raises(IntegrityError):
            uni2.rel = rel
            uni2.other_rel = other_rel
            sleep(1)
            uni2.save()

    def test_unique_delete(self):
        self.prepare_testbed()
        rel = UniqRelation().save()
        u = Uniques(id='qwe', rel=rel, username='bar').blocking_save()
        u_id, u_username = u.id, u.username
        u.blocking_delete()
        p = Uniques(id='qwe', rel=rel, username='bar').blocking_save()
        assert u_id == p.id
        assert u_username == p.username
        assert rel == p.rel



