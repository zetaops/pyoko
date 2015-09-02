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

raw_form_output = [{'name': 'auth_info.email', 'title': 'Email', 'default': None, 'storage': 'Node',
                    'section': 'AuthInfo', 'required': True, 'type': 'string',
                    'value': 'suuper@suup.com'},
                   {'name': 'auth_info.password', 'title': 'Password', 'default': None,
                    'storage': 'Node', 'section': 'AuthInfo', 'required': True, 'type': 'string',
                    'value': '123'},
                   {'name': 'auth_info.username', 'title': 'Username', 'default': None,
                    'storage': 'Node', 'section': 'AuthInfo', 'required': True, 'type': 'string',
                    'value': 'foo_user'},
                   {'name': 'bio', 'title': 'Biography', 'default': None, 'storage': 'main',
                    'section': 'main', 'required': True, 'type': 'text_general',
                    'value': 'Lorem impsum dolar sit amet falan filan'},
                   {'name': 'join_date', 'title': 'Join Date', 'default': None, 'storage': 'main',
                    'section': 'main', 'required': True, 'type': 'date',
                    'value': datetime.date(2015, 5, 16)},
                   {'name': 'name', 'title': 'First Name', 'default': None, 'storage': 'main',
                    'section': 'main', 'required': True, 'type': 'text_tr', 'value': 'Jack'},
                   {'name': 'number', 'title': 'Student No', 'default': None, 'storage': 'main',
                    'section': 'main', 'required': True, 'type': 'string', 'value': '20300344'},
                   {'name': 'pno', 'title': 'TC No', 'default': None, 'storage': 'main',
                    'section': 'main', 'required': True, 'type': 'string', 'value': '2343243433'},
                   {'name': 'surname', 'title': 'Last Name', 'default': None, 'storage': 'main',
                    'section': 'main', 'required': True, 'type': 'text_tr', 'value': 'Black'}]

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
    {'value': '', 'name': 'password', 'storage': 'main',
     'default': None, 'type': 'password', 'section': 'main',
     'required': True, 'title': 'Password'},
    {'value': '', 'name': 'username', 'storage': 'main', 'default': None,
     'type': 'string', 'section': 'main', 'required': True,
     'title': 'Username'}
]

output_of_test_list_node_with_linked_model = [
    {'name': 'name', 'title': 'Name', 'default': None, 'storage': 'main', 'section': 'main',
     'required': True, 'type': 'string', 'value': u'Employee Manager'},
    {'content': [
        {'name': 'codename', 'title': 'Codename', 'default': None, 'storage': 'main',
         'section': 'main', 'required': True, 'type': 'string', 'value': u'employee.all'},
        {'name': 'name', 'title': 'Name', 'default': None, 'storage': 'main', 'section': 'main',
         'required': True, 'type': 'string', 'value': u'Can see employee data'}],
     'name': 'permission_id',
     'title': 'Permission',
     'default': None,
     'section': 'main',
     'required': None,
     'type': 'model',
     'model_name': 'Permission',
     'value': u'D3Tu8VE0EqxgZfEGMnLdbJilQuk'},
    {'name': 'permissions.idx', 'title': '', 'default': None, 'storage': 'ListNode',
     'section': 'Permissions', 'required': True, 'type': 'string',
     'value': u'164647af596647cfaa5ad1ab1c84714e'}]


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
        output_of_test_list_node_with_linked_model[1]['value'] = serialized_model[1]['value']
        output_of_test_list_node_with_linked_model[2]['value'] = serialized_model[2]['value']
        assert serialized_model == output_of_test_list_node_with_linked_model
