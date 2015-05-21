# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from pyoko.db.schema_update import SchemaUpdater
from tests.data.solr_schema import test_data_solr_fields, test_data_solr_schema
from tests.data.test_model import Student


def test_collect_index_fields():
    st = Student()
    result = st._collect_index_fields()
    print result
    assert result == test_data_solr_fields

def test_create_solr_schema():
    st = Student()
    fields = st._collect_index_fields()
    result = SchemaUpdater.create_schema(fields)
    print result
    assert result == test_data_solr_schema
