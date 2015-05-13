# -*-  coding: utf-8 -*-
"""
This file can be used as a scratchpad and be cleared / modified by anybody.
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from time import time


REPEAT_COUNT = 1000000

class Foo(object):
    obj_cache = {'a': {}, 'b': 12345, 'c': []}

    def __getattribute__(self, key):
        # if key in super(Foo, self).__getattribute__('obj_cache'):
        try:
            return object.__getattribute__(self, 'obj_cache')[key]
        # else:
        except KeyError:
            return object.__getattribute__(self, key)

class Boo(object):
    a = {}
    b = 12345
    c = []

f = Foo()
t1 = time()

for i in xrange(REPEAT_COUNT):

    f.a
    f.b
    f.c
t2 = round(time() - t1, 5)
print "getattribute %s times took %s sec" % (REPEAT_COUNT, t2)

f = Boo()
t1 = time()

for i in  xrange(REPEAT_COUNT):

    f.a
    f.b
    f.c
t3 = round(time() - t1, 5)
print "plain access %s times took %s sec" % (REPEAT_COUNT, t3)
