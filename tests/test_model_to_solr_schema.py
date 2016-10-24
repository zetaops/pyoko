# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from pyoko.conf import settings
from pyoko.db.schema_update import SchemaUpdater
from tests.data.solr_schema import test_data_solr_fields_debug_zero, test_data_solr_fields_debug_not_zero,\
    test_data_solr_schema_debug_zero, test_data_solr_schema_debug_not_zero
from tests.models import Student


def test_collect_index_fields():
    st = Student()
    result = st._collect_index_fields()
    sorted_result = sorted(result, key=lambda x: x[0])
    if not settings.DEBUG:
        sorted_data = sorted(test_data_solr_fields_debug_zero, key=lambda x: x[0])
        assert sorted_result == sorted_data

    else:
        sorted_data = sorted(test_data_solr_fields_debug_not_zero, key=lambda x: x[0])
        assert sorted_result == sorted_data


def test_create_solr_schema():
    st = Student()
    fields = st._collect_index_fields()
    result = SchemaUpdater.get_schema_fields(fields)
    if not settings.DEBUG:
        assert sorted(result) == sorted(test_data_solr_schema_debug_zero)

    else:
        assert sorted(result) == sorted(test_data_solr_schema_debug_not_zero)
