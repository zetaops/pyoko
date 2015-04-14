# -*-  coding: utf-8 -*-
"""
this module contains some methods to help testing search and data retrieval on Riak
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from lib.db.base import RiakDataAccess


class Seeker(RiakDataAccess):
    """
    this class sequantally extracts searchable field names and their actual values
    then tries to access same values by various features of Yokozuna API
    """

    def __init__(self, riak_client):
        super(Seeker, self).__init__(riak_client)
        self.search_objects = {}
        self.suffix = ''
        self.current_obj_id = None

    def get_search_items(self, suffix='_s'):
        self.suffix = suffix
        for pack in list(self.bucket.stream_keys()):
            for obj_id, obj in pack[0]:
                self.current_obj_id = obj_id
                self._extract_search_data(obj)

    def _extract_search_data(self, dct, key_name=''):
        for k, v in dct:
            if isinstance(v, dict):
                self._extract_search_data(v, key_name)
            elif k.endswith(self.suffix):
                self.search_objects[self.current_obj_id]['%s.%s' % (key_name, k)] = v

    def test_search(self, index):
        for k, v in self.search_objects:
            query = "%s:%s" % (k, v)
            result = self.bucket.search(query, index)
            print("Query: %s\n"
                  "Success: %s\n"
                  "Result: %s\n" %
                      (query, False, result))
