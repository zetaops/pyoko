"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from time import sleep
from tests.models import Student
from pyoko.db.connection import cache
import ast
import six

"""
Environmental Variable ENABLE_CACHING should be set as True before
running the tests.

"""


class TestCase():

    def test_get_from_cache(self):

        s = Student().blocking_save()

        cached_value = ""
        clean_value = s._data

        sleep(2)

        try:
            cached_value = cache.get(s.key)
        except:
            pass

        if six.PY3:
            cached_value = cached_value.decode()

        cached_value_d = ast.literal_eval(cached_value)

        for key in cached_value_d.keys():
            assert cached_value_d[key] == clean_value[key]


        # To make sure the data is read from cache while key is in it
        try:
            cache.set(s.key, "a")
            assert Student.objects.get(s.key) == "a"
        except:
            pass











