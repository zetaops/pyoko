# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from importlib import import_module
import os
from pprint import pprint
from pyoko.db.schema_update import SchemaUpdater
from pyoko.manage import ManagementCommands
from tests.data.solr_schema import test_data_solr_fields, test_data_solr_schema
from tests.models import Student
from pyoko.db.connection import http_client as client
import sys

def test_collect_index_fields():
    st = Student()
    result = st._collect_index_fields()
    sorted_result =sorted(result, key=lambda x: x[0])
    sorted_data = sorted(test_data_solr_fields, key=lambda x: x[0])
    # pprint(sorted_data)
    # pprint(sorted_result)
    assert sorted_result == sorted_data


def test_create_solr_schema():
    st = Student()
    fields = st._collect_index_fields()
    result = SchemaUpdater.get_schema_fields(fields)
    assert sorted(result) == sorted(test_data_solr_schema)

def test_apply_solr_schema():
    # import_module('models')
    mc = ManagementCommands()
    mc.parse_args(['update_schema', '--bucket', 'student'])
    mc.schema_update()
    assert all(list(zip(*mc.robot.report))[1])
