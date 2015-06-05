# -*-  coding: utf-8 -*-
"""
data models for tests
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from pyoko.db.schema_update import SchemaUpdater
from pyoko.model import Model, Node, ListNode
from pyoko import field


class Student(Model):
    # def __init__(self, **kwargs):
        # We define model relations in __init__ method, because Python parser raises a NameError
        # if we refer to a not yet defined class in body of another class.
        # self.contact_info = ContactInfo()
        # super(Student, self).__init__(**kwargs)
    # contact_info = ContactInfo()

    # def row_level_access(self):
    #     self.objects = self.objects.filter(user_in=self._context.user['id'],)



    class Meta(object):
        # bucket = 'student'
        # store = True
        cell_filters = {
            # fields will be filtered out if self._context.perms does not
            # contain the given permission.
            # permission            : ['field','list']
            'can_view_student_phone': ['phone']
        }

    number = field.String(index=True)
    pno = field.String(index=True)
    name = field.String(index_as='text_tr')
    surname = field.String(index_as='text_tr')
    join_date = field.Date(index=True)
    bio = field.Text(index=True)

    class AuthInfo(Node):
        username = field.String(index=True)
        email = field.String(index=True)
        password = field.String()

        class Meta(object):
            required = False

    class Lectures(ListNode):
        name = field.String(index_as='text_tr')
        code = field.String(required=False, index=True)
        credit = field.Integer(default=0, index=True)

        class NodeInListNode(Node):
            foo = field.String()

        class Exams(ListNode):
            type = field.String()
            date = field.Date()
            point = field.Integer(store=False)

            class Meta(object):
                required = False

        class Attendance(ListNode):
            date = field.Date()
            hour = field.Integer()
            attended = field.Boolean(default=False)


class ContactInfo(Node):
    class Addresses(ListNode):
        class Meta(object):
            required = False

        name = field.String()
        street = field.String()
        town = field.String()
        city = field.String(index=True)
        postal_code = field.Integer(index=True)

    class Phones(ListNode):
        gsm = field.String()
        land_line = field.String()

