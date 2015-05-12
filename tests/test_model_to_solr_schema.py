# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from tests.data.solr_schema import test_data_solr_fields
from tests.data.test_model import Student


def test_collect_index_fields():
    st = Student()
    result = st._collect_index_fields()
    print "||||||||||>>>>>", result
    assert result == test_data_solr_fields
