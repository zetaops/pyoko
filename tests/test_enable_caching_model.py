"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

from tests.models import Student
from pyoko.db.connection import cache
import json
import six
from pyoko import settings


class TestCase():

    def test_get_from_cache(self):
        if settings.ENABLE_CACHING:
            s = Student().blocking_save()

            cached_value = ""
            clean_value = s._data

            try:
                cached_value = cache.get(s.key)
            except:
                pass

            if six.PY3:
                cached_value = cached_value.decode()

            cached_value_d = json.loads(cached_value)

            for key in cached_value_d.keys():
                assert cached_value_d[key] == clean_value[key]


            # To make sure the data is read from cache while key is in it
            try:
                cache.set(s.key, "a")
                assert Student.objects.get(s.key) == "a"
            except:
                pass

            s.blocking_delete()

            try:
                assert not cache.get(s.key)
            except:
                pass













