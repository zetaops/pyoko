# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import datetime
import time
import six
from pyoko.exceptions import ValidationError


# class Link(object):
#     def __init__(self, model,  reverse=False):
#         self.reverse = reverse
#         self.model =
from pyoko.conf import settings


class BaseField(object):
    link_type = False
    default_value = None

    def __init__(self, default=None, required=False, index=False,  index_as=None, store=settings.SOLR_STORE_ALL):
        self.required = required
        self.index_as = index_as
        self.index = index or bool(index_as)
        self.store = store
        self.default = default
        self.name = ''

        # self._updated = False  # user set or updated the value
        # self._fetched = False  # value loaded from solr or riak
    #
    # def set_value(self, value):
    #     self._updated = self.validate(value)
    #     self.value = value

    def __get__(self, instance, cls=None):
        # return self
        # print "GET___", self.value, instance, cls
        if cls is None:
            return self
        return instance._field_values.get(self.name, None)

    def __set__(self, instance, value):
        # print "__set__ called for : ", self, value
        # self._updated = self.validate(value)
        instance._field_values[self.name] = value

    def __delete__(self,instance):
        raise AttributeError("Can't delete attribute")

    def clean_value(self, val):
        if val is None:
            val = self.default() if callable(self.default) else self.default
        return val

    def validate(self, val):
        return True


# class Dict(BaseField):
#     pass


class String(BaseField):
    # def __init__(self, *args, **kwargs):
    #     super(String, self).__init__(*args, **kwargs)
    pass

class Text(BaseField):
    pass

class Boolean(BaseField):
    pass

class DateTime(BaseField):
    FORMAT_STRING = '%Y-%m-%dT%H:%M:%SZ'
    def __init__(self, *args, **kwargs):
        super(DateTime, self).__init__(*args, **kwargs)
        self.default = lambda: time.strftime(self.FORMAT_STRING)

    def clean_value(self, val):
        if val is None:
            return self.default() if callable(self.default) else self.default
        else:
            return val.strftime("%Y-%m-%dT%H:%M:%SZ")

    def __set__(self, instance, value):
        if isinstance(value, six.string_types):
            value = datetime.datetime.strptime(value, self.FORMAT_STRING)
        instance._field_values[self.name] = value


class Date(DateTime):
    FORMAT_STRING = '%Y-%m-%dT00:00:00Z'

    # def __init__(self, *args, **kwargs):
    #     super(Date, self).__init__(*args, **kwargs)
    #     self.default = lambda: time.strftime('%Y-%m-%dT00:00:00Z')
    #
    # def clean_value(self, val):
    #     if val is None:
    #         return self.default() if callable(self.default) else self.default
    #     else:
    #         return val.strftime("%Y-%m-%dT00:00:00Z")


class Integer(BaseField):
    default_value = 0

    def clean_value(self, val):
        val = val or self.default_value
        try:
            return int(val)
        except ValueError:
            raise ValidationError("%r could not be cast to integer" % val)
