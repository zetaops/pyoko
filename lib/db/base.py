# -*-  coding: utf-8 -*-
"""
this module contains a base class for other db access classes
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import riak
import time
from connection import client

class MultipleObjectsReturned(Exception):
    """The query returned multiple objects when only one was expected."""
    pass

class RiakDataAccess(object):
    def __init__(self, riak_client=client, index=None):
        # , get_all_data=False
        # self.get_all_data = get_all_data
        self.client = riak_client
        self.index = index
        self.bucket_name = None
        self.bucket_type = None
        self.result_set = []
        self.bucket = riak.RiakBucket

    def set_bucket(self, type, name):
        self.bucket_type = type
        self.bucket_name = name
        self.bucket = self.client.bucket_type(self.bucket_type).bucket(self.bucket_name)
        return self

    @staticmethod
    def _timeit(method, round_by=1):
        start_time = time.time()
        method()
        end_time = time.time()
        return round(end_time - start_time, round_by)

    def count_bucket(self):
        return sum([len(key_list) for key_list in self.bucket.stream_keys()])

    def _delete_all(self):
        count = self.count_bucket()
        for pck in self.bucket.stream_keys():
            for k in pck:
                self.bucket.get(k).delete()
        return count

    def count(self):
        return self.result_set['num_found']

    def all(self):
        return [self.bucket.get(r['_yz_rk']) for r in self.result_set['docs']]

    def get(self):
        if self.count() > 1:
            raise MultipleObjectsReturned()
        return self.bucket.get(self.result_set['docs'][0]['_yz_rk'])

    def results(self):
        return self.result_set['docs']

    def _query(self, query):
        self.result_set = self.bucket.search(query, self.index)
        return self

    # def _pack_up(self, result):
    #     """
    #     if it's enough for us return self.just_indexed_data)
    #     otherwise get the whole objects from riak.
    #     :param result: dict, riak search resultset
    #     :return: dict, brief or full result set
    #     """
    #     if not self.just_indexed_data:
    #         return result['docs']
    #     else:
    #         return self.all(result)

