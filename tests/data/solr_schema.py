# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

test_data_solr_fields = [
    ('bio', 'text_general', True, True, False),
    ('archived', 'boolean', True, True, False),
    ('surname', 'text_tr', True, True, False),
    ('name', 'text_tr', True, True, False),
    ('timestamp', 'long', True, True, False),
    ('number', 'string', True, True, False),
    ('deleted', 'boolean', True, False, False),
    ('join_date', 'date', True, True, False),
    ('pno', 'string', True, True, False),
    ('lectures.credit', 'int', True, True, True),
    ('lectures.code', 'string', True, True, True),
    ('lectures.name', 'text_tr', True, True, True),
    ('lectures.attendance.date', 'date', False, True, True),
    ('lectures.attendance.attended', 'boolean', False, True, True),
    ('lectures.attendance.hour', 'int', False, True, True),
    ('lectures.exams.date', 'date', False, True, True),
    ('lectures.exams.point', 'int', False, False, True),
    ('lectures.exams.type', 'string', False, True, True),
    ('lectures.node_in_list_node.foo', 'string', False, True, True),
    ('auth_info.username', 'string', True, True, False),
    ('auth_info.password', 'string', False, True, False),
    ('auth_info.email', 'string', True, True, False)
]

test_data_solr_schema = [
    '<field type="text_general" name="bio"  indexed="true" stored="true" multiValued="false" />',
    '<field type="boolean" name="archived"  indexed="true" stored="true" multiValued="false" />',
    '<field type="text_tr" name="surname"  indexed="true" stored="true" multiValued="false" />',
    '<field type="text_tr" name="name"  indexed="true" stored="true" multiValued="false" />',
    '<field type="long" name="timestamp"  indexed="true" stored="true" multiValued="false" />',
    '<field type="string" name="number"  indexed="true" stored="true" multiValued="false" />',
    '<field type="boolean" name="deleted"  indexed="true" stored="false" multiValued="false" />',
    '<field type="date" name="join_date"  indexed="true" stored="true" multiValued="false" />',
    '<field type="string" name="pno"  indexed="true" stored="true" multiValued="false" />',
    '<field type="int" name="lectures.credit"  indexed="true" stored="true" multiValued="true" />',
    '<field type="int" name="lectures.exams.point"  indexed="false" stored="false" multiValued="true" />',
    '<field type="string" name="lectures.code"  indexed="true" stored="true" multiValued="true" />',
    '<field type="text_tr" name="lectures.name"  indexed="true" stored="true" multiValued="true" />',
    '<field type="date" name="lectures.attendance.date"  indexed="false" stored="true" multiValued="true" />',
    '<field type="boolean" name="lectures.attendance.attended"  indexed="false" stored="true" multiValued="true" />',
    '<field type="int" name="lectures.attendance.hour"  indexed="false" stored="true" multiValued="true" />',
    '<field type="date" name="lectures.exams.date"  indexed="false" stored="true" multiValued="true" />',
    '<field type="string" name="lectures.exams.type"  indexed="false" stored="true" multiValued="true" />',
    '<field type="string" name="lectures.node_in_list_node.foo"  indexed="false" stored="true" multiValued="true" />',
    '<field type="string" name="auth_info.username"  indexed="true" stored="true" multiValued="false" />',
    '<field type="string" name="auth_info.password"  indexed="false" stored="true" multiValued="false" />',
    '<field type="string" name="auth_info.email"  indexed="true" stored="true" multiValued="false" />']
