# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import sys
import os
import copy
import json
import re
import datetime
import random
from time import mktime
from uuid import uuid4
import importlib

UN_CAMEL_RE = re.compile('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')


class SimpleChoicesManager(object):
    # Untested, POC!
    def __call__(self, choices, key):
        return dict(choices).get(key)

    @staticmethod
    def get_all(choices):
        return choices

simple_choices_manager = SimpleChoicesManager()

class SimpleRiakFileManager(object):
    # Untested, POC!

    def store_file(self, **kw):
        return "%s/|%s" % (kw['ext'], kw['content'])

# Somehow I can't monkey-patch this from sphinx's conf.py
# So, this is the workaround I'm using for now...
if hasattr(sys, 'IN_SPHINX'):
    lazy_property = property
else:
    class lazy_property(object):
        """
        Meant to be used for lazy evaluation of an object attribute.
        property should represent non-mutable data, as it replaces itself.

        from: http://stackoverflow.com/a/6849299/454130
        """

        def __init__(self, fget):
            self.fget = fget
            self.func_name = fget.__name__

        def __get__(self, obj, cls):
            if obj is None:
                return None
            value = self.fget(obj)
            obj.__dict__[self.func_name] = value
            return value


def un_camel(input, dash="_"):
    return UN_CAMEL_RE.sub(r'%s\1' % dash, input).lower()


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


def getScriptPath():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def add_to_path():
    sys.path.append(os.path.dirname(getScriptPath()))

sys.IMPORT_CACHE = {}
def get_object_from_path(path):
    """
    Import's object from given Python path.
    """
    try:
        return sys.IMPORT_CACHE[path]
    except KeyError:
        _path = path.split('.')
        module_path = '.'.join(_path[:-1])
        class_name = _path[-1]
        module = importlib.import_module(module_path)
        sys.IMPORT_CACHE[path] = getattr(module, class_name)
        return sys.IMPORT_CACHE[path]


def pprnt(input, return_data=False):
    """
    Prettier print for nested data

    Args:
        input: Input data
        return_data (bool): Default False. Print outs if False, returns if True.
    Returns:
        None | Pretty formatted text representation of input data.
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[32m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    import json, re
    result = json.dumps(input, sort_keys=True, indent=4)
    result = re.sub(r'(")(\w*?_id)(":)', r'\1%s%s\2%s\3' % (BOLD, HEADER, ENDC), result)
    result = re.sub(r'(")(\w*?_set)(":)', r'\1%s%s\2%s\3' % (BOLD, HEADER, ENDC), result)
    result = re.sub(r'(\n *?")(\w*?)(":)', r'\1%s%s\2%s\3' % (BOLD, OKGREEN, ENDC), result)
    if not return_data:
        print(result)
    else:
        return result
