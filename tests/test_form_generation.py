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
from pyoko.form import ModelForm, Form
from tests.data.test_data import data, clean_data

from tests.models import *

raw_form_output = [{'default': None,
                    'fields': [{'default': None,
                                'name': 'auth_info.username',
                                'required': True,
                                'title': 'Username',
                                'type': 'string',
                                'value': 'foo_user'},
                               {'default': None,
                                'name': 'auth_info.password',
                                'required': True,
                                'title': 'Password',
                                'type': 'string',
                                'value': '123'},
                               {'default': None,
                                'name': 'auth_info.email',
                                'required': True,
                                'title': 'Email',
                                'type': 'string',
                                'value': 'suuper@suup.com'}],
                    'models': [],
                    'name': 'AuthInfo',
                    'required': None,
                    'title': 'AuthInfo',
                    'type': 'Node',
                    'value': '!'},
                   {'default': None,
                    'name': 'bio',
                    'required': True,
                    'title': 'Biography',
                    'type': 'text_general',
                    'value': 'Lorem impsum dolar sit amet falan filan'},
                   {'default': None,
                    'name': 'join_date',
                    'required': True,
                    'title': 'Join Date',
                    'type': 'date',
                    'value': datetime.date(2015, 5, 16)},
                   {'default': None,
                    'name': 'name',
                    'required': True,
                    'title': 'First Name',
                    'type': 'text_tr',
                    'value': 'Jack'},
                   {'default': None,
                    'name': 'number',
                    'required': True,
                    'title': 'Student No',
                    'type': 'string',
                    'value': '20300344'},
                   {'default': None,
                    'name': 'pno',
                    'required': True,
                    'title': 'TC No',
                    'type': 'string',
                    'value': '2343243433'},
                   {'default': None,
                    'name': 'surname',
                    'required': True,
                    'title': 'Last Name',
                    'type': 'text_tr',
                    'value': 'Black'}]

received_data = {
    'auth_info.email': 'duuper@suup.com',
    'auth_info.password': '1111',
    'auth_info.username': 'poser',
    'bio': "You think water moves fast? You should see ice. It moves like it has a mind. "
           "Like it knows it killed the world once and got a taste for murder. "
           "After the avalanche, it took us a week to climb out.",
    'join_date': datetime.date(2015, 5, 16),
    'name': 'Samuel',
    'deleted': False,
    'number': '20300344',
    'timestamp': None,
    'pno': '2343243433',
    'surname': 'Jackson'}


class LoginForm(Form):
    TYPE_OVERRIDES = {
        'password': 'password'
    }
    username = field.String("Username")
    password = field.String("Password")


serialized_login_form = [
    {'value': '', 'name': 'password', 'default': None,
     'type': 'password', 'required': True, 'title': 'Password'},
    {'value': '', 'name': 'username', 'default': None,
     'type': 'string', 'required': True, 'title': 'Username'}
]

linked_model_out = [{'default': None,
                     'fields': [{'default': None,
                                 'name': 'permissions.idx',
                                 'required': True,
                                 'title': '',
                                 'type': 'string',
                                 'value': u'164647af596647cfaa5ad1ab1c84714e'}],
                     'models': [{'content': [{'default': None,
                                              'name': 'codename',
                                              'required': True,
                                              'title': 'Codename',
                                              'type': 'string',
                                              'value': u'employee.all'},
                                             {'default': None,
                                              'name': 'name',
                                              'required': True,
                                              'title': 'Name',
                                              'type': 'string',
                                              'value': u'Can see employee data'}],
                                 'default': None,
                                 'model_name': 'Permission',
                                 'name': 'permission_id',
                                 'required': None,
                                 'title': 'permission',
                                 'type': 'model',
                                 'value': u'D3Tu8VE0EqxgZfEGMnLdbJilQuk'}],
                     'name': 'Permissions',
                     'required': None,
                     'title': 'Permissions',
                     'type': 'ListNode',
                     'value': '!'},
                    {'default': None,
                     'name': 'name',
                     'required': True,
                     'title': 'Name',
                     'type': 'string',
                     'value': u'Employee Manager'}]


# noinspection PyMethodMayBeStatic
class TestCase:
    cleaned_up = False

    @classmethod
    def clean(cls):
        if not cls.cleaned_up:
            for model in [Student, ]:
                model.objects._clear_bucket()
            sleep(2)
            cls.cleaned_up = True

    def test_modelform_serialize_simple(self):
        self.clean()
        student = Student()
        student.set_data(clean_data)
        student.save()
        serialized_model = sorted(ModelForm(student)._serialize(), key=lambda d: d['name'])
        # print("============================")
        # pprint(serialized_model)
        assert raw_form_output == serialized_model

    def test_plain_form(self):
        serialized_model = sorted(LoginForm()._serialize(), key=lambda d: d['name'])
        assert serialized_model == serialized_login_form

    def test_plain_form_deserialize(self):
        login_data = {'username': 'Samuel', 'password': 'seeice'}
        model = LoginForm().deserialize(login_data)
        assert model.password == login_data["password"]
        assert model.username == login_data["username"]

    def test_modelform_deserialize_simple(self):
        self.clean()
        student = ModelForm(Student()).deserialize(received_data)
        student.save()
        sleep(1)
        db_student = Student.objects.filter(auth_info__email=received_data['auth_info.email']).get()
        assert db_student.AuthInfo.email == received_data['auth_info.email']
        assert db_student.bio == received_data['bio']

    def test_list_node_with_linked_model(self):
        arole = AbstractRole.objects.filter()[0]
        serialized_model = sorted(ModelForm(arole, all=True)._serialize(), key=lambda d: d['name'])
        # print("=====================================")
        # pprint(serialized_model)
        # print("=====================================")
        assert linked_model_out[0]['models'][0]['content'][0]['name'] == 'codename'

        assert linked_model_out[1]['value'] == serialized_model[1]['value']
