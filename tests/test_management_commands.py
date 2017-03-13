# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

import codecs
from time import sleep
from pyoko.manage import ManagementCommands
from .models import Person, User
import tempfile
import os


def test_load_dump_data():
    path = '/tmp/load_dump.csv'
    ManagementCommands(args=['dump_data', '--model', 'Student', '--path', path])
    with codecs.open(path, encoding='utf-8') as file:
        out = file.read()
    ManagementCommands(args=['load_data', '--update', '--path', path])
    sleep(1)
    ManagementCommands(args=['dump_data', '--model', 'Student', '--path', path])
    with codecs.open(path, encoding='utf-8') as file:
        assert len(out) == len(file.read())


def test_dump_per_model():
    # Test if the per model dumps work
    path = tempfile.mkdtemp(prefix='pyoko_test_')
    ManagementCommands(args=['dump_data',
                             '--model', 'Person,User',
                             '--path', path,
                             '--per_model'])
    # Make sure the dumps were created
    person_path = os.path.join(path, 'Person.csv')
    assert os.path.isfile(person_path)
    user_path = os.path.join(path, 'User.csv')
    assert os.path.isfile(user_path)
    # Check if the dumps contain correct students
    with codecs.open(person_path) as person_file:
        persons_dumped = person_file.read()
    assert Person.objects.count() > 0
    for person in Person.objects:
        assert person.key in persons_dumped
    # Check if the dumps contain correct users
    with codecs.open(user_path) as user_file:
        users_dumped = user_file.read()
    assert User.objects.count() > 0
    for user in User.objects:
        assert user.key in users_dumped


def test_dump_json():
    # Test if the per model dumps work
    handle, path = tempfile.mkstemp(prefix='pyoko_test_', suffix='.json')
    ManagementCommands(args=['dump_data',
                             '--model', 'Person,User',
                             '--path', path,
                             '--type', 'json'])
    # Check if the dump contains correct students
    with codecs.open(path) as file_:
        data_dumped = file_.read()
    assert Person.objects.count() > 0
    for person in Person.objects:
        assert person.key in data_dumped
    # Check if the dump contains correct users
    assert User.objects.count() > 0
    for user in User.objects:
        assert user.key in data_dumped


def test_dump_json_tree():
    # Test if the per model dumps work
    handle, path = tempfile.mkstemp(prefix='pyoko_test_', suffix='.json')
    ManagementCommands(args=['dump_data',
                             '--model', 'Person,User',
                             '--type', 'json_tree',
                             '--path', path])
    # Check if the dump contains correct students
    with codecs.open(path) as file_:
        data_dumped = file_.read()
    assert Person.objects.count() > 0
    for person in Person.objects:
        assert person.key in data_dumped
    # Check if the dump contains correct users
    assert User.objects.count() > 0
    for user in User.objects:
        assert user.key in data_dumped


def test_dump_pretty():
    # Test if the per model dumps work
    handle, path = tempfile.mkstemp(prefix='pyoko_test_', suffix='.json')
    ManagementCommands(args=['dump_data',
                             '--model', 'Person,User',
                             '--path', path,
                             '--type', 'pretty'])
    # Check if the dump contains correct students
    with codecs.open(path) as file_:
        data_dumped = file_.read()
    assert Person.objects.count() > 0
    for person in Person.objects:
        assert person.key in data_dumped
    # Check if the dump contains correct users
    assert User.objects.count() > 0
    for user in User.objects:
        assert user.key in data_dumped


def test_apply_solr_schema():
    # TODO: Currently only tests if it's running without giving any errors, should assert something
    ManagementCommands(args=['migrate', '--model', 'Student', '--force'])

def test_flush_db():
    # TODO: Currently only tests if it's running without giving any errors, should assert something
    ManagementCommands(args=['flush_model', '--model', 'Student'])
