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
from connection import *
from lib.py2map import Dictomap
from lib.utils import DotDict


class MultipleObjectsReturned(Exception):
    """The query returned multiple objects when only one was expected."""
    pass


# TODO: Add simple query caching
# TODO: Add OR support

class RiakDataAccess(object):
    """

    """

    def __init__(self, riak_client=None, **config):
        # , get_all_data=False
        # self.get_all_data = get_all_data
        self.client = riak_client or pbc_client
        self.config = DotDict(config)
        self.bucket_name = None
        self.bucket_type = None
        self.solr_result_set = []
        self.search_query = set()
        self.search_params = {}
        self.result_cache = []
        self.bucket = riak.RiakBucket
        self.datatype = None
        self.last_query_string = ''
        self.return_solr_result = False


    def set_bucket(self, type, name):
        self.bucket_type = type
        self.bucket_name = name
        self.bucket = self.client.bucket_type(self.bucket_type).bucket(self.bucket_name)
        if 'index' not in self.config:
            self.config.index = self.bucket_name
        self.datatype = self.bucket.get_properties().get('datatype', None)
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
        """
        just for development, normally we should never delete anything, let alone whole bucket!
        """
        count = self.count_bucket()
        for pck in self.bucket.stream_keys():
            for k in pck:
                self.bucket.get(k).delete()
        return count

    def count(self):
        self._exec_query(rows=0)
        return self.solr_result_set['num_found']

    def all(self):
        self.conf(fl='_yz_rk')
        return self

    def get(self):
        self._exec_query()
        if self.count() > 1:
            raise MultipleObjectsReturned()
        return self._get()

    def _get(self):
        self._exec_query()
        result = self.bucket.get(self.solr_result_set['docs'][0]['_yz_rk'])
        self.reset()
        return result

    def solr(self):
        """
        returns raw solr result set
        """
        self._exec_query()
        self.return_solr_result = True
        return self

    def filter(self, **filters):
        """
        this will support OR and other more advanced queries as well
        """
        self.reset()
        for key, val in filters.items():
            key = key.replace('__', '.')
            if val is None:
                key = '-%s' % key
                val = '[* TO *]'
            self.search_query.add("%s:%s" % (key, val))
        return self

    def reset(self):
        self.solr_result_set = []
        self.search_params = {}
        self.search_query.clear()

    def _query(self, query):
        self.search_query.add(query)
        self.reset()
        return self

    def save(self, key, value):
        if self.datatype == 'map' and isinstance(value, dict):
            return Dictomap(self.bucket, value, str(key)).map.store()
        else:
            return self.bucket.new(key, value).store()

    def _compile_query(self):
        """
        this will support OR and other more advanced queries as well
        :return: Solr query string
        """
        return ' AND '.join(self.search_query)

    def __getitem__(self, index):
        if isinstance(index, int):
            self.conf(rows=1, start=index)
            return self._get()
        elif isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            self.conf(rows=stop - start, start=start)
            return self
        else:
            raise TypeError("index must be int or slice")

    def _get_from_db(self):
        self.reset()
        return self.bucket.multiget(map(lambda k: k['_yz_rk'], self.solr_result_set['docs']))

    def __iter__(self):
        self._exec_query()
        self.reset()
        return iter(self._get_from_db() if not self.return_solr_result else self.solr_result_set)


    def conf(self, **params):
        """
        solr query parameters
        """
        self.search_params.update(params)
        return self

    def _exec_query(self, **params):
        self.search_params.update(params)
        query_string = self._compile_query()
        print "query str", query_string
        if query_string != self.last_query_string:
            print( "yess, exec")
            self.last_query_string = query_string
            self.solr_result_set = self.bucket.search(query_string, self.config.index, **self.search_params)
        return self

