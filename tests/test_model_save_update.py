# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from time import sleep
from tests.data.test_data import data
from tests.models import *


class TestCase:
    """
    sleep() s are required to give enough time to yokozuna for update solr index
    """
    cleaned_up = False
    index_checked = False

    @classmethod
    def prepare_testbed(cls, reset=False):
        if (not cls.cleaned_up) or reset:
            for model in [Student]:
                model.objects._clear_bucket()
            sleep(2)
            cls.cleaned_up = True

    # def test_one_to_one_simple_benchmarked(self, benchmark):
    #     benchmark(self.test_one_to_one_simple)

    def test_get_or_create(self):
        self.prepare_testbed()
        defaults = dict(name="Foo", surname="Fee")
        pno = '123456'
        st, is_new = Student.objects.get_or_create(defaults=defaults, pno=pno)
        assert is_new == True
        assert st.name == defaults['name']
        assert st.pno == pno
        sleep(1)
        st, is_new = Student.objects.get_or_create(defaults=defaults, pno=pno)
        assert is_new == False
        assert st.name == defaults['name']
        assert st.pno == pno

        st, is_new = Student.objects.get_or_create(**defaults)
        assert is_new == False
        assert st.name == defaults['name']
        assert st.pno == pno

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
