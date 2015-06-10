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
                                      'date': datetime.date(2015, 5, 9),
                                      'hour': 2},
                                     {'attended': True,
                                      'date': datetime.date(2015, 5, 10),
                                      'hour': 4}],
                      'Exams': [{'date': datetime.date(2015, 5, 11),
                                 'point': 65,
                                 'type': 'Q'}],
                      'NodeInListNode': {'foo': 'FOOOO'},
                      'code': 'math101',
                      'credit': 4,
                      'name': 'Introduction to Math'},
                     {'Attendance': [{'attended': False,
                                      'date': datetime.date(2015, 5, 13),
                                      'hour': 2},
                                     {'attended': True,
                                      'date': datetime.date(2015, 5, 14),
                                      'hour': 4}],
                      'Exams': [{'date': datetime.date(2015, 5, 15),
                                 'point': 65,
                                 'type': 'Q'}],
                      'NodeInListNode': {'foo': 'FOOOO'},
                      'code': 'rock101',
                      'credit': 10,
                      'name': 'Introduction to Rocking'}],
        'bio': "Lorem impsum dolar sit amet falan filan",
        'join_date': datetime.date(2015, 5, 16),
        'name': 'Jack',
        'archived': False,
        '_deleted': False,
        'number': '20300344',
        'timestamp': None,
        'pno': '2343243433',
        'surname': 'Black'}


clean_data = {'AuthInfo': {'email': 'suuper@suup.com',
                     'password': '123',
                     'username': 'foo_user'},
        'Lectures': [{'Attendance': [{'attended': False,
                                      'date': datetime.date(2015, 5, 9).strftime('%Y-%m-%dT00:00:00Z'),
                                      'hour': 2},
                                     {'attended': True,
                                      'date': datetime.date(2015, 5, 10).strftime('%Y-%m-%dT00:00:00Z'),
                                      'hour': 4}],
                      'Exams': [{'date': datetime.date(2015, 5, 11).strftime('%Y-%m-%dT00:00:00Z'),
                                 'point': 65,
                                 'type': 'Q'}],
                      'NodeInListNode': {'foo': 'FOOOO'},
                      'code': 'math101',
                      'credit': 4,
                      'name': 'Introduction to Math'},
                     {'Attendance': [{'attended': False,
                                      'date': datetime.date(2015, 5, 13).strftime('%Y-%m-%dT00:00:00Z'),
                                      'hour': 2},
                                     {'attended': True,
                                      'date': datetime.date(2015, 5, 14).strftime('%Y-%m-%dT00:00:00Z'),
                                      'hour': 4}],
                      'Exams': [{'date': datetime.date(2015, 5, 15).strftime('%Y-%m-%dT00:00:00Z'),
                                 'point': 65,
                                 'type': 'Q'}],
                      'NodeInListNode': {'foo': 'FOOOO'},
                      'code': 'rock101',
                      'credit': 10,
                      'name': 'Introduction to Rocking'}],
        'bio': "Lorem impsum dolar sit amet falan filan",
        'join_date': datetime.date(2015, 5, 16).strftime('%Y-%m-%dT00:00:00Z'),
        'name': 'Jack',
        'archived': False,
        '_deleted': False,
        'number': '20300344',
        'timestamp': None,
        'pno': '2343243433',
        'surname': 'Black'}


# qs = Student.objects.filter(name='Jack',lectures__attandance__attended=False)

# Student.objects
