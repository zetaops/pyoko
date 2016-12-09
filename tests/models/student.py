# -*-  coding: utf-8 -*-
"""
data models for tests
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from pyoko import Model, ListNode, field, Node
from .users import Role

class Student(Model):
    # def __init__(self, **kwargs):
        # We define model relations in __init__ method, because Python parser raises a NameError
        # if we refer to a not yet defined class in body of another class.
        # self.contact_info = ContactInfo()
        # super(Student, self).__init__(**kwargs)
    # contact_info = ContactInfo()

    # def row_level_access(self):
    #     self.objects = self.objects.filter(user_in=self._context.user['id'],)


    number = field.String("Student No", index=True)
    pno = field.String("TC No", index=True)
    name = field.String("First Name", type='text_tr', index=False)
    surname = field.String("Last Name", type='text_tr', index=False)
    join_date = field.Date("Join Date", index=True)
    bio = field.Text("Biography", index=True)

    class AuthInfo(Node):
        username = field.String("Username")
        email = field.String("Email")
        password = field.String("Password", index=False)

    class Lectures(ListNode):
        name = field.String(type='text_tr')
        code = field.String(required=False)
        credit = field.Integer(default=0)
        role = Role('Role_1', index=True,reverse_link=True)

        class NodeInListNode(Node):
            foo = field.String(index=False)

        class Exams(ListNode):
            type = field.String(index=False)
            date = field.Date(index=False)
            point = field.Integer(index=False)

        class Attendance(ListNode):
            date = field.Date(index=False)
            hour = field.Integer(index=False)
            attended = field.Boolean(default=False, index=False)

    class Lecturer(ListNode):
        role = Role('Role_2', index=True,reverse_link=True)




