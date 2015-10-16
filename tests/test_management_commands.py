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


def test_load_dump_data():
    path = '/tmp/load_dump.csv'
    ManagementCommands(args=['dump_data', '--model', 'Student', '--file', path])
    with codecs.open(path, encoding='utf-8') as file:
        out = file.read()
    ManagementCommands(args=['load_data', '--update', '--file', path])
    sleep(1)
    ManagementCommands(args=['dump_data', '--model', 'Student', '--file', path])
    with codecs.open(path, encoding='utf-8') as file:
        assert out == file.read()

def test_apply_solr_schema():
    # TODO: Currently only tests if it's running without giving any errors, should assert something
    ManagementCommands(args=['migrate', '--model', 'Student', '--force'])

def test_flush_db():
    # TODO: Currently only tests if it's running without giving any errors, should assert something
    ManagementCommands(args=['flush_model', '--model', 'Student'])
