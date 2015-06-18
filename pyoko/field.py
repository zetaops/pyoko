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
from pyoko.conf import settings

DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
DATE_FORMAT = "%Y-%m-%dT00:00:00Z"


class BaseField(object):
    link_type = False
    default_value = None

    def __init__(self,
                 default=None,
                 required=False,
                 index=False,
                 index_as=None,
                 store=settings.SOLR_STORE_ALL,):
        self.required = required
        self.index_as = index_as
        self.index = index or bool(index_as)
        self.store = store
        self.default = default
        self.name = ''

    def __get__(self, instance, cls=None):
        if cls is None:
            return self
        return instance._field_values.get(self.name, None)

    def __set__(self, instance, value):
        instance._field_values[self.name] = value

    def __delete__(self, instance):
        raise AttributeError("Can't delete attribute")

    def clean_value(self, val):
        if val is None:
            val = self.default() if callable(self.default) else self.default
        return val

    def validate(self, val):
        return True


class String(BaseField):
    pass


class Text(BaseField):
    pass


class Boolean(BaseField):
    pass


class DateTime(BaseField):
    def __init__(self, format=DATE_TIME_FORMAT, *args, **kwargs):
        super(DateTime, self).__init__(*args, **kwargs)
        self.format = format
        self.default = lambda: time.strftime(self.format)

    def clean_value(self, val):
        if val is None:
            return self.default() if callable(self.default) else self.default
        else:
            return val.strftime(self.format)

    def __set__(self, instance, value):
        if isinstance(value, six.string_types):
            value = datetime.datetime.strptime(value, self.format)
        instance._field_values[self.name] = value


class Date(DateTime):
    def __init__(self, format=DATE_FORMAT, *args, **kwargs):
        super(Date, self).__init__(format=format, *args, **kwargs)


class Integer(BaseField):
    default_value = 0

    def clean_value(self, val):
        val = val or self.default_value
        try:
            return int(val)
        except ValueError:
            raise ValidationError("%r could not be cast to integer" % val)
