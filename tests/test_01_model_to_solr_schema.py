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

# FIXME: schema update/creation runs multithreaded
# if we run this -fake- test before other db related ones,
# we can be sure that it's working as expected.
def tXXXXXXXXXXXXXXXXXXest_apply_solr_schema():
    mc = ManagementCommands()
    mc.parse_args(['update_schema', '--silent', '--bucket', 'all'])
    mc.schema_update()
    # sleep(20)  # riak probably will need some time to apply schema updates
    # to other nodes. but we need to investigate how much time required
    #

