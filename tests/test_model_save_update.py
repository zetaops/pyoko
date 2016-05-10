# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from time import sleep

from pyoko.manage import FlushDB
from tests.data.test_data import data
from .models import Student


class TestCase:
    """
    sleep() s are required to give enough time to yokozuna for update solr index
    """
    cleaned_up = False
    index_checked = False

    @classmethod
    def prepare_testbed(cls, reset=False):
        if (not cls.cleaned_up) or reset:
            FlushDB(model='Student').run()
            cls.cleaned_up = True

    # def test_one_to_one_simple_benchmarked(self, benchmark):
    #     benchmark(self.test_one_to_one_simple)

    def test_get_or_create(self):
        self.prepare_testbed()
        defaults = dict(name="Foo", surname="Fee")
        pno = '123456'
        st, is_new = Student.objects.get_or_create(defaults=defaults, pno=pno)
        assert is_new
        assert st.name == defaults['name']
        assert st.pno == pno
        sleep(1)
        st2, is_new = Student.objects.get_or_create(defaults=defaults, pno=pno)
        assert is_new == False
        assert st2.name == defaults['name']
        assert st2.pno == pno

        st3, is_new = Student.objects.get_or_create(**defaults)
        assert is_new == False
        assert st3.name == defaults['name']
        assert st3.pno == pno

    def test_update_with_partial_data(self):
        self.prepare_testbed()
        student = Student().set_data(data)
        student.save()
        db_student = Student.objects.get(student.key)
        db_student.surname = 'Freeman'
        db_student.save()
        updated_db_student = Student.objects.filter().get(db_student.key)
        assert updated_db_student.surname == db_student.surname
        assert updated_db_student.name == student.name
