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




UN_CAMEL_RE = re.compile('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')


def un_camel(input):
    return UN_CAMEL_RE.sub(r'_\1', input).lower()

def to_camel(s):
    return re.sub(r'(?!^)_([a-zA-Z])', lambda m: m.group(1).upper(), s)

def grayed(*args):
    return '\033[1;37m%s\033[1;m' % ' '.join(map(str, args))

class MyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return int(mktime(obj.timetuple()))

        return json.JSONEncoder.default(self, obj)


def random_word(length):
   return ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(length))
