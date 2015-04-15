# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from lib.db.base import RiakDataAccess


class Student(RiakDataAccess):
    """
    contains common db access patterns for Student bucket
    usage:
    stdnt = Student().set_bucket(type='student', name='student4')
    stdnt.by_tcno('10623465730').get()
    stdnt.by_city('Kon*').all()
    """
    def __init__(self):
        super(Student, self).__init__()
        self.conf.index = 'student2'
        self.set_bucket('student', 'student5')


    def by_id(self, student_id):
        return self.bucket.get(str(student_id))

    def by_tcno(self, student_id):
        return self.filter(identity_information__tc_no_l=student_id)


    def by_city(self, city):
        return self.filter(contact_information__addresses__city_ss=city)


    def with_unpaid_fees(self):
        return self.filter(payment_information__tuition_fees__unpaid_ss=None)
