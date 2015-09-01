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

raw_form_output = [
    {'storage': 'Node', 'default': None, 'name': 'auth_info.email', 'section': 'AuthInfo',
     'required': True, 'value': '', 'type': 'string', 'title': 'Email'},
    {'storage': 'Node', 'default': None, 'name': 'auth_info.password', 'section': 'AuthInfo',
     'required': True, 'value': '', 'type': 'string', 'title': 'Password'},
    {'storage': 'Node', 'default': None, 'name': 'auth_info.username', 'section': 'AuthInfo',
     'required': True, 'value': '', 'type': 'string', 'title': 'Username'},
    {'storage': 'main', 'default': None, 'name': 'bio', 'section': 'main', 'required': True,
     'value': 'Lorem impsum dolar sit amet falan filan', 'type': 'text_general',
     'title': 'Biography'},
    {'storage': 'main', 'default': None, 'name': 'join_date', 'section': 'main',
     'required': True, 'value': datetime.date(2015, 5, 16), 'type': 'date', 'title': 'Join Date'},
    {'storage': 'main', 'default': None, 'name': 'name', 'section': 'main', 'required': True,
     'value': 'Jack', 'type': 'text_tr', 'title': 'First Name'},
    {'storage': 'main', 'default': None, 'name': 'number', 'section': 'main', 'required': True,
     'value': '20300344', 'type': 'string', 'title': 'Student No'},
    {'storage': 'main', 'default': None, 'name': 'pno', 'section': 'main', 'required': True,
     'value': '2343243433', 'type': 'string', 'title': 'TC No'},
    {'storage': 'main', 'default': None, 'name': 'surname', 'section': 'main', 'required': True,
     'value': 'Black', 'type': 'text_tr', 'title': 'Last Name'}]

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
