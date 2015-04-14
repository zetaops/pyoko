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


class RiakDataAccess(object):
    def __init__(self, riak_client, index='student', just_indexed_data=False):
        self.client = riak_client
        self.index = index
        self.bucket_name = None
        self.bucket_type = None
        self.bucket = riak.RiakBucket
        self.light = just_indexed_data

    def set_bucket(self, bucket_type, bucket_name):
        self.bucket_type = bucket_type
        self.bucket_name = bucket_name
        self.bucket = self.client.bucket_type(self.bucket_type).bucket(self.bucket_name)
        return self

    def timeit(self, method, round_by=1):
        start_time = time.time()
        method()
        end_time = time.time()
        return round(end_time - start_time, round_by)

    def count_keys(self):
        return sum([len(key_list) for key_list in self.bucket.stream_keys()])

    def delete_all(self):
        count = self.count_keys()
        for pck in self.bucket.stream_keys():
            for k in pck:
                self.bucket.get(k).delete()
        return count

    def bring_whole_objects(self, result_set):
        return [self.bucket.get(r['_yz_rk']) for r in result_set['docs']]

    def pack_up(self, result):
        if self.light:
            return result['docs']
        else:
            return self.bring_whole_objects(result)

