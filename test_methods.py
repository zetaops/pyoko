# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from thread import start_new_thread

from connection import client
from schemas import make_student_data

bucket = client.bucket('my_bucket')


def generate_students():
    student = make_student_data()


def save_students():
    student = make_student_data()
    std_obj = bucket.new(student['identity_information']['tc_no'], student)
    std_obj.store()


def range_save_students():
    for i in range(100):
        save_students()


def multi_save_students():
    for i in range(10):
        start_new_thread(range_save_students, ())
