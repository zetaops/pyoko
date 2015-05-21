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
from time import mktime


class DotDict(dict):
    def __getattr__(self, attr):
        if attr.startswith('__'):
            raise AttributeError(attr)
        return self[attr]

    def __deepcopy__(self, memo):
        return DotDict(copy.deepcopy(dict(self)))

    def __key(self):
        return tuple((k, self[k]) for k in sorted(self))

    def __hash__(self):
        return hash(self.__key())

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__



UN_CAMEL_RE = re.compile('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')


def un_camel(input):
    return UN_CAMEL_RE.sub(r'_\1', input).lower()


def grayed(*args):
    return '\033[1;37m%s\033[1;m' % ' '.join(map(str, args))

class MyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return int(mktime(obj.timetuple()))

        return json.JSONEncoder.default(self, obj)

