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
from pyoko.settings import SOLR_STORE_ALL


class BaseField(object):
    link_type = False
    default_value = None

    def __init__(self, required=False, index=False, default=None, store=SOLR_STORE_ALL):
        self.required = required
        self.index = index
        self.store = store
        self.value = default or self.default_value
        self._updated = False  # user set or updated the value
        self._fetched = False  # value loaded from solr or riak

    def set_value(self, value):
        self._updated = self.validate(value)
        self.value = value

    def __get__(self, instance, cls=None):
        return instance.value

    def __set__(self, instance, value):
        instance._updated = self.validate(value)
        instance.value = value

    def __delete__(self,instance):
        raise AttributeError("Can't delete attribute")

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

class Text(BaseField):

    def __repr__(self):
        return "Text field with value %s..." % self.value[:40]

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
            raise ValidationError("%r could not be cast to integer" % (self.value,))

    def __repr__(self):
        return "Integer field with value %s" % self.value


