# -*-  coding: utf-8 -*-
"""
data models for tests
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from pyoko.model import Model, ListModel
from pyoko import field


class Student(Model):
    def __init__(self, **kwargs):

        # We define model relations in __init__ method, because Python parser raises a NameError
        # if we refer to a not yet defined class in body of another class.
        self.contact_info = ContactInfo()
        super(Student, self).__init__(**kwargs)

    class Meta(object):
        bucket = 'student'


    number = field.String(index=True)
    pno = field.String(index=True)
    name = field.String(index='tr')
    surname = field.String(index='tr')
    join_date = field.Date(index=True)

    class AuthInfo(Model):
        username = field.String(index=True)
        email = field.String(index=True)
        password = field.String()

        class Meta(object):
            required = False

    class Lectures(ListModel):
        name = field.String(index='tr')
        code = field.String(required=False, index=True)
        credit = field.Integer(default=0, index=True)

        class ModelInListModel(Model):
            foo = field.String

        class Exams(ListModel):
            type = field.String()
            date = field.Date()
            point = field.Integer()

            class Meta(object):
                required = False

        class Attendance(ListModel):
            date = field.Date()
            hour = field.Integer()
            attended = field.Boolean(default=False)


class ContactInfo(Model):
    class Addresses(ListModel):
        class Meta(object):
            required = False

        name = field.String()
        street = field.String()
        town = field.String()
        city = field.String()
        postal_code = field.Integer()


    class Phones(ListModel):
        gsm = field.String()
        land_line = field.String()


# s = Student()
# c = ContactInfo()
# c.Addresses()

