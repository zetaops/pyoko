# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from time import sleep

from tests.models.perm_tests import *


class TestCase:
    """
    tests for format parameter of date/datetime fields
    """
    cleaned_up = False


    @classmethod
    def prepare_testbed(cls):
        if not cls.cleaned_up:
            for model in [Person,]:
                clean_count = model.objects._clear_bucket()
            if clean_count:
                sleep(2)
            cls.cleaned_up = True


    def test_row_based_acl(self):
        self.prepare_testbed()
        context = MockContext()
        Person(context, name='p1', section='Section_A', phone='90232').save()
        Person(context, name='p2', section='Section_A', phone='902321').save()
        Person(context, name='p3', section='Section_B', phone='9023212').save()
        sleep(1)
        assert Person(context).objects.count() == 3
        context.restrict('access_to_other_sections')
        assert Person(context).objects.count() == 2
        assert Person(context).objects.filter(section='Section_B').count() == 0
        context.grant('access_to_other_sections')
        assert Person(context).objects.filter(section='Section_B').count() == 1



    def test_field_permissions(self):
        self.prepare_testbed()
        context = MockContext()
        orig_phone = '90232'
        p = Person(context, name='p1', section='Section_A', phone=orig_phone).save()
        assert Person(context).objects.get(p.key).phone == orig_phone
        context.restrict('can_see_phone_number')
        assert Person(context).objects.get(p.key).phone == None
        p = Person(context).objects.get(p.key)
        p.phone = '123'
        p.save()
        context.grant('can_see_phone_number')
        assert Person(context).objects.get(p.key).phone == orig_phone



