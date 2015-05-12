# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

test_data_solr_fields = [('bio', 'Text', None, True, True, False),
                         ('surname', 'String', 'text_tr', True, True, False),
                         ('name', 'String', 'text_tr', True, True, False),
                         ('number', 'String', None, True, True, False),
                         ('join_date', 'Date', None, True, True, False),
                         ('pno', 'String', None, True, True, False),
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
