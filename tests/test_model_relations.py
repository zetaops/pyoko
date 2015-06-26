# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from time import sleep
from pyoko.manage import ManagementCommands
from tests.data.test_data import data, clean_data, solr_doc
from tests.models import *


class TestModelRelations:
    """
    tests for many to one, one to one functionalities of pyoko
    """
    cleaned_up = False
    index_checked = False
    model_list = [User, Employee] # Unit,Location,

    @classmethod
    def preprocess(cls):
        if not cls.cleaned_up:
            for model in cls.model_list:
                model.objects._clear_bucket()
            sleep(2)
            cls.cleaned_up = True

    @classmethod
    def prepare_testbed(cls):
        cls.preprocess()


    def test_one_to_one_simple(self):
        self.prepare_testbed()
        name = 'Joe'
        position = 'Coder'
        user = User(name=name)
        user.save()
        employee = Employee(role=position, usr=user)
        employee.save()
        sleep(1)
        db_employee = Employee.objects.filter(role=position).get()
        assert db_employee.usr.name == name

