#!/usr/bin/env python
# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import timeit
import riak
from riak.security import SecurityCreds
from schemas import make_student_data

creds = SecurityCreds(username='esat', password='qwe-asd', cacert_file='riak.crt')
# client = riak.RiakClient(protocol='pbc', host='62.210.245.199', pb_port='8087', credentials=creds)
client = riak.RiakClient(protocol='pbc', host='62.210.245.199', pb_port='8087')
# client = riak.RiakClient(protocol='http', host='62.210.245.199', http_port='8098')
bucket = client.bucket('my_bucket')
# print bucket.get('onee', notfound_ok=True)
# bucket.new_from_file


def save_students():
    student = make_student_data()
    std_obj = bucket.new(student['identity_information']['tc_no'], student)
    std_obj.store()


# print timeit.timeit('save_students()', number=1000)