# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

test_data_solr_fields = [('bio', 'Text', None, True, True, False), ('archived', 'Boolean', None, True, True, False),
                         ('surname', 'String', 'text_tr', True, True, False),
                         ('name', 'String', 'text_tr', True, True, False),
                         ('timestamp', 'Date', None, True, True, False), ('number', 'String', None, True, True, False),
                         ('_deleted', 'Boolean', None, True, False, False),
                         ('join_date', 'Date', None, True, True, False), ('pno', 'String', None, True, True, False),
                         ('lectures.credit', 'Integer', None, True, True, True),
                         ('lectures.code', 'String', None, True, True, True),
                         ('lectures.name', 'String', 'text_tr', True, True, True),
                         ('attendance.date', 'Date', None, False, True, True),
                         ('attendance.attended', 'Boolean', None, False, True, True),
                         ('attendance.hour', 'Integer', None, False, True, True),
                         ('exams.date', 'Date', None, False, True, True),
                         ('exams.type', 'String', None, False, True, True),
                         ('modelinlistmodel.foo', 'String', None, False, True, False),
                         ('authinfo.username', 'String', None, True, True, False),
                         ('authinfo.password', 'String', None, False, True, False),
                         ('authinfo.email', 'String', None, True, True, False)]

test_data_solr_schema = ['<field type="text" name="bio"  indexed="true" stored="true" multivalued="false" />',
                         '<field type="boolean" name="archived"  indexed="true" stored="true" multivalued="false" />',
                         '<field type="text_tr" name="surname"  indexed="true" stored="true" multivalued="false" />',
                         '<field type="text_tr" name="name"  indexed="true" stored="true" multivalued="false" />',
                         '<field type="date" name="timestamp"  indexed="true" stored="true" multivalued="false" />',
                         '<field type="string" name="number"  indexed="true" stored="true" multivalued="false" />',
                         '<field type="boolean" name="_deleted"  indexed="true" stored="false" multivalued="false" />',
                         '<field type="date" name="join_date"  indexed="true" stored="true" multivalued="false" />',
                         '<field type="string" name="pno"  indexed="true" stored="true" multivalued="false" />',
                         '<field type="integer" name="lectures.credit"  indexed="true" stored="true" multivalued="true" />',
                         '<field type="string" name="lectures.code"  indexed="true" stored="true" multivalued="true" />',
                         '<field type="text_tr" name="lectures.name"  indexed="true" stored="true" multivalued="true" />',
                         '<field type="date" name="attendance.date"  indexed="false" stored="true" multivalued="true" />',
                         '<field type="boolean" name="attendance.attended"  indexed="false" stored="true" multivalued="true" />',
                         '<field type="integer" name="attendance.hour"  indexed="false" stored="true" multivalued="true" />',
                         '<field type="date" name="exams.date"  indexed="false" stored="true" multivalued="true" />',
                         '<field type="string" name="exams.type"  indexed="false" stored="true" multivalued="true" />',
                         '<field type="string" name="modelinlistmodel.foo"  indexed="false" stored="true" multivalued="false" />',
                         '<field type="string" name="authinfo.username"  indexed="true" stored="true" multivalued="false" />',
                         '<field type="string" name="authinfo.password"  indexed="false" stored="true" multivalued="false" />',
                         '<field type="string" name="authinfo.email"  indexed="true" stored="true" multivalued="false" />']
