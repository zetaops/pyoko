# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import copy
import json
import re
import datetime
import random
from time import mktime
from uuid import uuid4

UN_CAMEL_RE = re.compile('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')


class lazy_property(object):
    '''
    from: http://stackoverflow.com/a/6849299/454130
    meant to be used for lazy evaluation of an object attribute.
    property should represent non-mutable data, as it replaces itself.
    '''

    def __init__(self, fget):
        self.fget = fget
        self.func_name = fget.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return None
        value = self.fget(obj)
        setattr(obj, self.func_name, value)
        return value

def un_camel(input):
    return UN_CAMEL_RE.sub(r'_\1', input).lower()

def un_camel_id(input):
    """
    uncamel for id fields
    :param input:
    :return:
    """
    return un_camel(input) + '_id'

def to_camel(s):
    """
    :param string s: under_scored string to be CamelCased
    :return: CamelCase version of input
    :rtype: str
    """
    # r'(?!^)_([a-zA-Z]) original regex wasn't process first groups
    return re.sub(r'_([a-zA-Z])', lambda m: m.group(1).upper(), '_' + s)

def grayed(*args):
    return '\033[1;37m%s\033[1;m' % ' '.join(map(str, args))

class MyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return int(mktime(obj.timetuple()))

        return json.JSONEncoder.default(self, obj)


def random_word(length):
   return ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(length))
