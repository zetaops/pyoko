# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from pprint import pprint
from pyoko.db.schema_update import SchemaUpdater
from tests.data.solr_schema import test_data_solr_fields, test_data_solr_schema
from tests.data.test_model import Student


def test_collect_index_fields():
    st = Student()
    result = st._collect_index_fields()
    assert sorted(result, key=lambda x: x[0]) == sorted(test_data_solr_fields,
                                                        key=lambda x: x[0])


def test_create_solr_schema():
    st = Student()
    fields = st._collect_index_fields()
    result = SchemaUpdater.create_schema(fields)
    # print result
    assert sorted(result) == sorted(test_data_solr_schema)
