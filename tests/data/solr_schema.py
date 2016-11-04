# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

test_data_solr_fields_debug_zero = [
    ('bio', 'text_general', True, False, False),
    ('surname', 'text_tr', True, False, False),
    ('name', 'text_tr', True, False, False),
    ('timestamp', 'date', True, False, False),
    ('updated_at', 'date', True, False, False),
    ('number', 'string', True, False, False),
    ('deleted', 'boolean', True, False, False),
    ('deleted_at', 'date', True, False, False),
    ('join_date', 'date', True, False, False),
    ('pno', 'string', True, False, False),
    ('lectures.credit', 'int', True, False, True),
    ('lectures.code', 'string', True, False, True),
    ('lectures.name', 'text_tr', True, False, True),
    ('lectures.attendance.date', 'date', False, False, True),
    ('lectures.attendance.attended', 'boolean', False, False, True),
    ('lectures.attendance.hour', 'int', False, False, True),
    ('lectures.exams.date', 'date', False, False, True),
    ('lectures.exams.point', 'int', False, False, True),
    ('lectures.exams.type', 'string', False, False, True),
    ('lectures.node_in_list_node.foo', 'string', False, False, True),
    ('lectures.role_id', 'string', True, False, True),
    ('lecturer.role_id', 'string', True, False, True),
    ('auth_info.username', 'string', True, False, False),
    ('auth_info.password', 'string', False, False, False),
    ('auth_info.email', 'string', True, False, False)
]

test_data_solr_fields_debug_not_zero = [(x, y, z, True, w) for x, y, z, q, w in test_data_solr_fields_debug_zero]

test_data_solr_schema_debug_zero = [
    '<field    type="text_general" name="bio"  indexed="true" stored="false" multiValued="false" />',
    '<field    type="text_tr" name="surname"  indexed="true" stored="false" multiValued="false" />',
    '<field    type="text_tr" name="name"  indexed="true" stored="false" multiValued="false" />',
    '<field    type="date" name="timestamp"  indexed="true" stored="false" multiValued="false" />',
    '<field    type="date" name="updated_at"  indexed="true" stored="false" multiValued="false" />',
    '<field    type="string" name="number"  indexed="true" stored="false" multiValued="false" />',
    '<field    type="boolean" name="deleted"  indexed="true" stored="false" multiValued="false" />',
    '<field    type="date" name="join_date"  indexed="true" stored="false" multiValued="false" />',
    '<field    type="string" name="pno"  indexed="true" stored="false" multiValued="false" />',
    '<field    type="int" name="lectures.credit"  indexed="true" stored="false" multiValued="true" />',
    '<field    type="int" name="lectures.exams.point"  indexed="false" stored="false" multiValued="true" />',
    '<field    type="string" name="lectures.code"  indexed="true" stored="false" multiValued="true" />',
    '<field    type="text_tr" name="lectures.name"  indexed="true" stored="false" multiValued="true" />',
    '<field    type="date" name="lectures.attendance.date"  indexed="false" stored="false" multiValued="true" />',
    '<field    type="boolean" name="lectures.attendance.attended"  indexed="false" stored="false" multiValued="true" />',
    '<field    type="date" name="deleted_at"  indexed="true" stored="false" multiValued="false" />',
    '<field    type="int" name="lectures.attendance.hour"  indexed="false" stored="false" multiValued="true" />',
    '<field    type="date" name="lectures.exams.date"  indexed="false" stored="false" multiValued="true" />',
    '<field    type="string" name="lectures.exams.type"  indexed="false" stored="false" multiValued="true" />',
    '<field    type="string" name="lectures.node_in_list_node.foo"  indexed="false" stored="false" multiValued="true" />',
    '<field    type="string" name="lectures.role_id"  indexed="true" stored="false" multiValued="true" />',
    '<field    type="string" name="lecturer.role_id"  indexed="true" stored="false" multiValued="true" />',
    '<field    type="string" name="auth_info.username"  indexed="true" stored="false" multiValued="false" />',
    '<field    type="string" name="auth_info.password"  indexed="false" stored="false" multiValued="false" />',
    '<field    type="string" name="auth_info.email"  indexed="true" stored="false" multiValued="false" />']

test_data_solr_schema_debug_not_zero = [
    '<field    type="text_general" name="bio"  indexed="true" stored="true" multiValued="false" />',
    '<field    type="text_tr" name="surname"  indexed="true" stored="true" multiValued="false" />',
    '<field    type="text_tr" name="name"  indexed="true" stored="true" multiValued="false" />',
    '<field    type="date" name="timestamp"  indexed="true" stored="true" multiValued="false" />',
    '<field    type="date" name="updated_at"  indexed="true" stored="true" multiValued="false" />',
    '<field    type="string" name="number"  indexed="true" stored="true" multiValued="false" />',
    '<field    type="boolean" name="deleted"  indexed="true" stored="true" multiValued="false" />',
    '<field    type="date" name="join_date"  indexed="true" stored="true" multiValued="false" />',
    '<field    type="string" name="pno"  indexed="true" stored="true" multiValued="false" />',
    '<field    type="int" name="lectures.credit"  indexed="true" stored="true" multiValued="true" />',
    '<field    type="int" name="lectures.exams.point"  indexed="false" stored="true" multiValued="true" />',
    '<field    type="string" name="lectures.code"  indexed="true" stored="true" multiValued="true" />',
    '<field    type="text_tr" name="lectures.name"  indexed="true" stored="true" multiValued="true" />',
    '<field    type="date" name="lectures.attendance.date"  indexed="false" stored="true" multiValued="true" />',
    '<field    type="boolean" name="lectures.attendance.attended"  indexed="false" stored="true" multiValued="true" />',
    '<field    type="date" name="deleted_at"  indexed="true" stored="true" multiValued="false" />',
    '<field    type="int" name="lectures.attendance.hour"  indexed="false" stored="true" multiValued="true" />',
    '<field    type="date" name="lectures.exams.date"  indexed="false" stored="true" multiValued="true" />',
    '<field    type="string" name="lectures.exams.type"  indexed="false" stored="true" multiValued="true" />',
    '<field    type="string" name="lectures.node_in_list_node.foo"  indexed="false" stored="true" multiValued="true" />',
    '<field    type="string" name="auth_info.username"  indexed="true" stored="true" multiValued="false" />',
    '<field    type="string" name="auth_info.password"  indexed="false" stored="true" multiValued="false" />',
    '<field    type="string" name="auth_info.email"  indexed="true" stored="true" multiValued="false" />']
