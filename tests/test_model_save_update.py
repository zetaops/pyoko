# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from time import sleep

from pyoko.manage import FlushDB
from pyoko.exceptions import ObjectDoesNotExist
from pyoko.db.adapter.db_riak import BlockSave
from tests.data.test_data import data
from .models import Student, User
import pytest


class TestCase:
    """
    sleep() s are required to give enough time to yokozuna for update solr index
    """
    cleaned_up = False
    index_checked = False

    @classmethod
    def prepare_testbed(cls, reset=False):
        if (not cls.cleaned_up) or reset:
            FlushDB(model='Student', wait_sync=True).run()
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

    def test_get_or_none(self):
        self.prepare_testbed()
        defaults = dict(name="Foo3", surname="Fee3")
        pno = '0123456'
        st, is_new = Student.objects.get_or_create(defaults=defaults, pno=pno)
        assert is_new
        assert st.name == defaults['name']
        assert st.pno == pno
        sleep(1)

        defaults.update({'pno': '0123456'})

        st2 = Student.objects.get_or_none(**defaults)
        assert st2 is not None
        assert st2.pno == pno

        defaults.update({'pno': '0123456777'})
        st2 = Student.objects.get_or_none(**defaults)
        assert st2 is None

    def test_delete_if_exists(self):
        self.prepare_testbed()
        defaults = dict(name="Foo4", surname="Fee4")
        pno = '43210'
        st, is_new = Student.objects.get_or_create(defaults=defaults, pno=pno)
        assert is_new

        cond = Student.objects.delete_if_exists(**defaults)
        assert cond

        cond = Student.objects.delete_if_exists(**defaults)
        assert not cond

    def test_update_with_partial_data(self):
        self.prepare_testbed()
        student = Student().set_data(data)
        student.save()
        db_student = Student.objects.get(student.key)
        db_student.surname = 'Freeman'
        db_student.save()
        updated_db_student = Student.objects.all().get(db_student.key)
        assert updated_db_student.surname == db_student.surname
        assert updated_db_student.name == student.name

    def test_missing_relation_not_created(self):
        """
        When an object is created, if it has a relation to another object that
        is referenced with an id, but the other object doesn't actually exist,
        the object referenced in relation automatically gets created. See issue
        #5450.

        The correct behaviour here should be throwing an exception, as inserting
        an incorrect id is a likely mistake that the programmer might make.
        """
        # Create a user, giving it a relation that doesn't exist
        supervisor_key = 'this_user_doesnt_exist'
        user = User(name='TEST_USER', supervisor_id=supervisor_key)

        initial_user_count = User.objects.count()
        with BlockSave(User):
            with pytest.raises(ObjectDoesNotExist):
                user.save()
        final_user_count = User.objects.count()

        # The missing relation should not have been created
        assert final_user_count - initial_user_count == 1

        # Cleanup
        user.delete()
