# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from time import sleep
from pyoko.db.schema_update import SchemaUpdater
from pyoko.manage import ManagementCommands
from tests.data.solr_schema import test_data_solr_fields, test_data_solr_schema
from tests.models import Student

def test_collect_index_fields():
    st = Student()
    result = st._collect_index_fields()
    sorted_result =sorted(result, key=lambda x: x[0])
    sorted_data = sorted(test_data_solr_fields, key=lambda x: x[0])
    assert sorted_result == sorted_data


def test_create_solr_schema():
    st = Student()
    fields = st._collect_index_fields()
    result = SchemaUpdater.get_schema_fields(fields)
    assert sorted(result) == sorted(test_data_solr_schema)
