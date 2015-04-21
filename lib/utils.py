# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import copy
import re


class DotDict(dict):
    def __getattr__(self, attr):
        if attr.startswith('__'):
            raise AttributeError(attr)
        return self[attr]

    def __deepcopy__(self, memo):
        return DotDict(copy.deepcopy(dict(self)))

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

UN_CAMEL_RE = re.compile('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')


def un_camel(input):
    return UN_CAMEL_RE.sub(r'_\1', input).lower()


def grayed(*args):
    return '\033[1;37m%s\033[1;m' % ' '.join(map(str, args))
