# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import datetime
from pprint import pprint
from time import sleep
from pyoko.form import ModelForm
from tests.data.test_data import data

from tests.models import *

raw_form_output = [
    {'storage': 'main', 'default': False, 'name': 'archived', 'section': 'main', 'required': True,
     'value': False, 'type': 'boolean', 'title': ''},
    {'storage': 'Node', 'default': None, 'name': 'auth_info.email', 'section': 'AuthInfo',
     'required': True, 'value': '', 'type': 'string', 'title': 'Email'},
    {'storage': 'Node', 'default': None, 'name': 'auth_info.password', 'section': 'AuthInfo',
     'required': True, 'value': '', 'type': 'string', 'title': 'Password'},
    {'storage': 'Node', 'default': None, 'name': 'auth_info.username', 'section': 'AuthInfo',
     'required': True, 'value': '', 'type': 'string', 'title': 'Username'},
    {'storage': 'main', 'default': None, 'name': 'bio', 'section': 'main', 'required': True,
     'value': 'Lorem impsum dolar sit amet falan filan', 'type': 'text_general',
     'title': 'Biography'},
    {'storage': 'main', 'default': '', 'name': 'join_date', 'section': 'main',
     'required': True, 'value': datetime.date(2015, 5, 16), 'type': 'date', 'title': 'Join Date'},
    {'storage': 'main', 'default': None, 'name': 'name', 'section': 'main', 'required': True,
     'value': 'Jack', 'type': 'text_tr', 'title': 'First Name'},
    {'storage': 'main', 'default': None, 'name': 'number', 'section': 'main', 'required': True,
     'value': '20300344', 'type': 'string', 'title': 'Student No'},
    {'storage': 'main', 'default': None, 'name': 'pno', 'section': 'main', 'required': True,
     'value': '2343243433', 'type': 'string', 'title': 'TC No'},
    {'storage': 'main', 'default': None, 'name': 'surname', 'section': 'main', 'required': True,
     'value': 'Black', 'type': 'text_tr', 'title': 'Last Name'}]


class TestModelRelations:
    """
    """
    cleaned_up = False

    @classmethod
    def cleanup(cls):
        if not cls.cleaned_up:
            for model in [Student, ]:
                model.objects._clear_bucket()
            sleep(2)
            cls.cleaned_up = True

    def test_modelform_serialize_simple(self):
        self.cleanup()
        student = Student()
        student._load_data(data)
        student.save()
        serialized_model = sorted(ModelForm(student)._serialize(), key=lambda d: d['name'])
        assert raw_form_output == serialized_model
