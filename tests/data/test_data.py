# -*-  coding: utf-8 -*-
"""
data models for tests
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import datetime

data = {'AuthInfo': {'email': 'suuper@suup.com',
                     'password': '123',
                     'username': 'foo_user'},
        'Lectures': [{'Attendance': [{'attended': False,
                                      'date': datetime.date(2015, 5, 12),
                                      'hour': 2},
                                     {'attended': True,
                                      'date': datetime.date(2015, 5, 12),
                                      'hour': 4}],
                      'Exams': [{'date': datetime.date(2015, 5, 12),
                                 'point': 65,
                                 'type': 'Q'}],
                      'NodeInListNode': {'foo': 'FOOOO'},
                      'code': 'math101',
                      'credit': 4,
                      'name': 'Introduction to Math'},
                     {'Attendance': [{'attended': False,
                                      'date': datetime.date(2015, 5, 12),
                                      'hour': 2},
                                     {'attended': True,
                                      'date': datetime.date(2015, 5, 12),
                                      'hour': 4}],
                      'Exams': [{'date': datetime.date(2015, 5, 12),
                                 'point': 65,
                                 'type': 'Q'}],
                      'NodeInListNode': {'foo': 'FOOOO'},
                      'code': 'rock101',
                      'credit': 10,
                      'name': 'Introduction to Rocking'}],
        'bio': "Lorem impsum dolar sit amet falan filan",
        'join_date': datetime.date(2015, 5, 12),
        'name': 'Jack',
        'archived': False,
        '_deleted': False,
        'number': '20300344',
        'timestamp':'2015-04-21T14:05:39Z',
        'pno': '2343243433',
        'surname': 'Black'}





# qs = Student.objects.filter(name='Jack',lectures__attandance__attended=False)

# Student.objects
