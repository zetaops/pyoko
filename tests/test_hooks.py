# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from time import sleep

from tests.models import *



class TestCase:
    """
    tests for many to one, one to one functionalities of pyoko
    sleep() s are required to give enough time to yokozuna for update solr index
    """

    def test_save_hooks(self):
        u = User().save()
        e = Employee(name="Foo", usr=u).save()
        assert e.post_save_counter == 1
        assert e.pre_save_counter == 1
        assert e.post_creation_counter == 1
        e.save()
        assert e.post_save_counter == 2
        assert e.pre_save_counter == 2
        assert e.post_creation_counter == 1
        e.delete()
        assert e.post_save_counter == 1
        assert e.pre_save_counter == 1
        assert e.post_creation_counter == 1











