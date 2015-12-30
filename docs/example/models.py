# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

from pyoko import Model, Node, ListNode, field


class Permission(Model):
    name = field.String("Name", index=True)
    code = field.String("Code Name", index=True)

    class Meta:
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"

    def __unicode__(self):
        return "%s %s" % (self.name, self.code)




class Unit(Model):
    name = field.String("Name", index=True)
    address = field.String("Address", index=True, null=True, blank=True)

    class Meta:
        verbose_name = "Unit"
        verbose_name_plural = "Units"

    def __unicode__(self):
        return self.name


class Person(Model):
    first_name = field.String("Name", index=True)
    last_name = field.String("Surname", index=True)
    work = Unit(verbose_name="Work", reverse_name="workers")
    home = Unit(verbose_name="Home", reverse_name="residents")


    class ContactInfo(Node):
        address = field.String("Address", index=True, null=True, blank=True)
        city = field.String("City", index=True)
        phone = field.String("Phone", index=True)
        email = field.String("Email", index=True)

    class Permissions(ListNode):
        perm = Permission()

        def __unicode__(self):
            return self.perm

    def __unicode__(self):
        return "%s %s" % (self.first_name, self.last_name)

    def get_permission_codes(self):
        return [p.perm.code for p in self.Permissions]

    def add_permission(self, perm):
        self.Permissions(permission=perm)
        self.save()

    def has_permission(self, perm):
        return perm in self.Permissions

    def has_permission_code(self, perm_code):
        perm = Permission.object.get(code=perm_code)
        return self.has_permission(perm)


