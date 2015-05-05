# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from pyoko.exceptions import ValidationError


# class Link(object):
#     def __init__(self, model,  reverse=False):
#         self.reverse = reverse
#         self.model =

class BaseField(object):
    link_type = False
    default_value = None

    def __init__(self, required=False, index=False, default=None):
        self.required = required
        self.index = index
        self.value = default or self.default_value
        self._updated = False  # user set or updated the value
        self._fetched = False  # value loaded from solr or riak

    def set_value(self, value):
        self.value = value

    def clean_value(self):
        return self.value

    def validate(self, value):
        return True

    def __repr__(self):
        return self.value

# class Dict(BaseField):
#     pass


class String(BaseField):

    def __repr__(self):
        return "String field with value %s" % self.value

class Boolean(BaseField):

    def __repr__(self):
        return "Boolean field with value %s" % self.value

class Date(BaseField):
    def __repr__(self):
        return "Date field with value %s" % self.value


class Integer(BaseField):
    default_value = 0

    def clean_value(self):
        try:
            return int(self.value)
        except ValueError:
            raise ValidationError("%r could not be cast to integer" % (value,))

    def __repr__(self):
        return "Integer field with value %s" % self.value


