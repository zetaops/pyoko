# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from time import sleep
from tests.models import *


class TestModelRelations:
    """
    tests for many to one, one to one functionalities of pyoko
    sleep() s are required to give enough time to yokozuna for update solr index
    """
    cleaned_up = False
    index_checked = False


    @classmethod
    def preprocess(cls):
        if not cls.cleaned_up:
            for model in [User, Employee, Scholar, TimeTable]:
                model.objects._clear_bucket()
            sleep(2)
            cls.cleaned_up = True

    @classmethod
    def prepare_testbed(cls):
        cls.preprocess()

    # def test_one_to_one_simple_benchmarked(self, benchmark):
    #     benchmark(self.test_one_to_one_simple)

    def test_one_to_one_simple(self):
        self.prepare_testbed()
