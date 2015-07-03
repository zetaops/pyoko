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

raw_form_output = [{'default': None,
                    'name': 'number',
                    'required': True,
                    'section': 'main',
                    'storage': 'main',
                    'title': 'Student No',
                    'type': 'string',
                    'value': '20300344'},
                   {'default': 'Join Date',
                    'name': 'join_date',
                    'required': True,
                    'section': 'main',
                    'storage': 'main',
                    'title': '',
                    'type': 'date',
                    'value': datetime.date(2015, 5, 16)},
                   {'default': False,
                    'name': 'archived',
                    'required': True,
                    'section': 'main',
                    'storage': 'main',
                    'title': '',
                    'type': 'boolean',
                    'value': False},
                   {'default': None,
                    'name': 'pno',
                    'required': True,
                    'section': 'main',
                    'storage': 'main',
                    'title': 'TC No',
                    'type': 'string',
                    'value': '2343243433'},
                   {'default': None,
                    'name': 'surname',
                    'required': True,
                    'section': 'main',
                    'storage': 'main',
                    'title': 'Last Name',
                    'type': 'text_tr',
                    'value': 'Black'},
                   {'default': None,
                    'name': 'name',
                    'required': True,
                    'section': 'main',
                    'storage': 'main',
                    'title': 'First Name',
                    'type': 'text_tr',
                    'value': 'Jack'},
                   {'default': None,
                    'name': 'bio',
                    'required': True,
                    'section': 'main',
                    'storage': 'main',
                    'title': 'Biography',
                    'type': 'text_general',
                    'value': 'Lorem impsum dolar sit amet falan filan'},
                   {'default': None,
                    'name': 'auth_info.password',
                    'required': True,
                    'section': 'AuthInfo',
                    'storage': 'Node',
                    'title': 'Password',
                    'type': 'string',
                    'value': ''},
                   {'default': None,
                    'name': 'auth_info.email',
                    'required': True,
                    'section': 'AuthInfo',
                    'storage': 'Node',
                    'title': 'Email',
                    'type': 'string',
                    'value': ''},
                   {'default': None,
                    'name': 'auth_info.username',
                    'required': True,
                    'section': 'AuthInfo',
                    'storage': 'Node',
                    'title': 'Username',
                    'type': 'string',
                    'value': ''}]


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

    def test_from_model_instance_simple(self):
        self.cleanup()
        student = Student()
        student._load_data(data)
        student.save()
        counter = 0
        for itm in ModelForm(student).serialize():
            counter += 1
            for it in raw_form_output:
                if it['name'] == itm['name']:
                    assert it['default'] == itm['default']
                    assert it['required'] == itm['required']
                    assert it['storage'] == itm['storage']
                    assert it['section'] == itm['section']
                    assert it['title'] == itm['title']
                    assert it['type'] == itm['type']
                    assert it['value'] == itm['value']
        assert counter == len(raw_form_output)
        # pprint(list(ModelForm(Employee()).generate()))
