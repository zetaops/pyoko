# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from time import sleep

from tests.models.date_models import *


class TestModelRelations:
    """
    tests for many to one, one to one functionalities of pyoko
    sleep() s are required to give enough time to yokozuna for update solr index
    """
    cleaned_up = False
    index_checked = False

    @classmethod
    def prepare_testbed(cls):
        if not cls.cleaned_up:
            for model in [DateModel,]:
                model.objects._clear_bucket()
            sleep(2)
            cls.cleaned_up = True


    def test_date_formatting(self):
        self.prepare_testbed()
        date_model = DateModel(date_with_format='20.01.2001', name='foo').save()
        sleep(1)
        from_db = DateModel.objects.get()
        assert from_db.date_with_format == date_model.date_with_format

