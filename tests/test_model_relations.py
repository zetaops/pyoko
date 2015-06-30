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

    # def test_one_to_one_simple_benchmarked(self, benchmark):
    #     benchmark(self.test_one_to_one_simple)

    def test_one_to_one_simple(self):
        self.prepare_testbed()
        name = 'Joe'
        position = 'Coder'
        user = User(name=name)
        user.save()
        employee = Employee(role=position, usr=user)
        employee.save()
        sleep(1)
        employee_from_db = Employee.objects.filter(role=position).get()
        assert employee_from_db.usr.name == name
        user_from_db = User.objects.filter(name=name).get()
        user_from_db.name = 'Joen'
        user_from_db.save()
        sleep(1)
        employee_from_db = Employee.objects.filter(role=position).get()
        assert employee_from_db.usr.name == 'Joen'

