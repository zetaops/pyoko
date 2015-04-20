# -*-  coding: utf-8 -*-
"""
this module contains a base class for other db access classes
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from connection import *
from lib.py2map import Dictomap
from lib.utils import DotDict, grayed
from enum import Enum


class MultipleObjectsReturned(Exception):
    """The query returned multiple objects when only one was expected."""
    pass

# TODO: Add tests
# TODO: Implement basic functionality of "new" method
# TODO: Add schema support for "new" method
# TODO: Add OR support
# TODO: Implement schema migration for Riak JSON data
# TODO: Investigate queryResultWindowSize solr setting, see: http://bit.ly/1HzO0M3

ReturnType = Enum('ReturnType', 'Object Data Solr')


class SolRiakcess(object):
    """
    This class implements Django-esque query APIs with the aim of fusing Solr and Riak in a more pythonic way
    """

    def __init__(self, **config):
        self.bucket = riak.RiakBucket
        self._cfg = DotDict(config)
        self._cfg.client = self._cfg.client or pbc_client
        self.datatype = None  # we convert new object data according to bucket datatype, eg: Dictomaping for 'map' type

        self.return_type = self._cfg.get('return_type', ReturnType.Object)
        self.default_row_size = self._cfg.get('row_size', 1000)

        self.new_value = None  # value of the to be created by .new(**params).save(key)

        self.solr_result_set = {}  # caching solr results, for repeating calls
        self.solr_query = set()  # query parts, will be compiled before execution
        self.solr_params = {}  # solr search parameters. eg: rows, fl, start, sort etc.
        # All the following properties used for caching the previous query.
        self.solr_preceding_params = {}  # preceding solr search parameters. eg: rows, fl, start, sort etc.
        self.solr_preceding_query = ''  # previously executed solr query
        self.riak_cache = []  # caching riak result, for repeating iterations on same query
        self.re_fetch_from_riak = True  # if we get fresh results from solr
        self.return_methods = {
            ReturnType.Object: self._get_from_db,
            ReturnType.Data: self._get_data_from_db,
            ReturnType.Solr: self._get_from_solr
        }


    # ######## Development Methods  #########

    def watch(self, brief=False):

        print grayed("solr_result_set : ", len(self.solr_result_set) if brief else self.solr_result_set)
        print grayed("riak_cache : ", len(self.riak_cache) if brief else self.riak_cache)
        print grayed("solr_query : ", self.solr_query)
        print grayed("solr_params : ", self.solr_params)
        print grayed("last_query : ", self.solr_preceding_query)
        print grayed("re_fetch_from_riak : ", self.re_fetch_from_riak)
        print grayed("return_type : ", self.return_type)
        print grayed("new_value : ", self.new_value)
        print grayed("solr_preceding_params : ", self.solr_preceding_params)
        print grayed("solr_preceding_query : ", self.solr_preceding_query)
        return self

    def _clear_bucket(self):
        """
        for development purposes, normally we should never delete anything, let alone the whole bucket!
        """
        if not 'yes' == raw_input("Say yes if you really want to delete all records in this bucket % s:" % self.bucket):
            return
        count = self.count_bucket()
        for pck in self.bucket.stream_keys():
            for k in pck:
                self.bucket.get(k).delete()
        return count

    # ######## Python Magic  #########

    def __iter__(self):
        self._exec_query()
        # print "THIS IS ITER"
        return iter(self.return_methods[self.return_type]())


    def __len__(self):
        # self._exec_query()
        # print "THIS IS LEN"
        return self.count()

    def __getitem__(self, index):
        # print "THIS IS GETITEM"
        if isinstance(index, int):
            self.set_solr_conf(rows=1, start=index)
            return self._get()
        elif isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            self.set_solr_conf(rows=stop - start, start=start)
            return self
        else:
            raise TypeError("index must be int or slice")


    # ######## local methods #########






    # ######## Riak Methods  #########

    def set_bucket(self, type, name):
        self._cfg.bucket_type = type
        self._cfg.bucket_name = name
        self.bucket = self._cfg.client.bucket_type(self._cfg.bucket_type).bucket(self._cfg.bucket_name)
        if 'index' not in self._cfg:
            self._cfg.index = self._cfg.bucket_name
        self.datatype = self.bucket.get_properties().get('datatype', None)
        return self

    def count_bucket(self):
        return sum([len(key_list) for key_list in self.bucket.stream_keys()])

    def new(self, **kwargs):
        """
        this will populate a new object using kwargs on top of latest version of the object schema
        :param kwargs:
        :return:
        """
        raise NotImplemented

    def save(self, key, value=None):
        value = value or self.new_value
        if self.datatype == 'map' and isinstance(value, dict):
            return Dictomap(self.bucket, value, str(key)).map.store()
        else:
            return self.bucket.new(key, value).store()

    def refetch_required(self, flag=None):
        if flag is not None:
            self.re_fetch_from_riak = flag
        else:
            return self.re_fetch_from_riak or not self.riak_cache

    def _get_from_db(self):
        if self.refetch_required():
            if not self._cfg.get('multiget'):
                self.riak_cache = map(lambda k: self.bucket.get(k['_yz_rk']), self.solr_result_set['docs'])
            else:
                self.riak_cache = self.bucket.multiget(map(lambda k: k['_yz_rk'], self.solr_result_set['docs']))
        self.reset_query()
        return self.riak_cache

    def _get_data_from_db(self, data=False):
        if self.refetch_required():
            if self._cfg.get('multiget'):
                self.riak_cache = map(lambda o: o.data, self.bucket.multiget(
                    map(lambda k: k['_yz_rk'], self.solr_result_set['docs'])))
            else:
                self.riak_cache = map(lambda k: self.bucket.get(k['_yz_rk']).data, self.solr_result_set['docs'])
        self.reset_query()
        return self.riak_cache

    def _get(self):
        self._exec_query()
        if self.refetch_required() and self.return_type in (ReturnType.Object, ReturnType.Data):
            self.riak_cache = [self.bucket.get(self.solr_result_set['docs'][0]['_yz_rk'])]

        if self.return_type == ReturnType.Object:
            return self.riak_cache[0]
        elif self.return_type == ReturnType.Data:
            return self.riak_cache[0].data
        else:
            return self.solr_result_set['docs'][0]


    def data(self):
        """
        a convience method for returning only data attributes of riak objects.
        """
        self.return_riak_data = True
        return self

    # ######## Solr/Query Related Methods  #########

    def filter(self, **filters):
        """
        this will support OR and other more advanced queries as well
        """
        for key, val in filters.items():
            key = key.replace('__', '.')
            if val is None:
                key = '-%s' % key
                val = '[* TO *]'
            self.solr_query.add("%s:%s" % (key, val))
        return self

    def all(self):
        self.set_solr_conf(fl='_yz_rk')
        return self

    def get(self):
        self._exec_query()
        print "THIS IS Get"
        if self.count() > 1:
            raise MultipleObjectsReturned()
        return self._get()

    def count(self):
        if not self.solr_result_set:
            self._exec_query(rows=0)
        return self.solr_result_set.get('num_found', -1)

    def reset_query(self):
        # self.solr_result_set.clear()
        self.solr_params = {}
        self.return_type = self._cfg.get('return_type', ReturnType.Object)
        self.solr_query.clear()

    def _query(self, query):
        self.solr_query.add(query)
        return self

    def set_solr_conf(self, **params):
        """
        add/update solr query parameters
        """
        self.solr_params.update(params)
        return self

    def fields(self, *args):  # riak client needs _yz_rk to distinguish between old and new search API.
        self.solr_params.update({'fl': ' '.join(set(args + ('_yz_rk',)))})
        return self

    def solr(self):
        """
        returns raw solr result
        """
        self.return_type = 3
        return self

    def data(self):
        """
        return data instead of riak object(s)
        """
        self.return_type = 2
        return self

    def _compile_query(self):
        """
        this will support "OR" and maybe other more advanced queries as well
        :return: Solr query string
        """
        # if not self.solr_query:
        # self.solr_query.add('*:*')  # get/count everything
        # elif len(self.solr_query) > 1 and '*:*' in self.solr_query:
        #     self.solr_query.remove('*:*')
        anded = ' AND '.join(self.solr_query)
        query = anded
        return query


    def _process_params(self, **params):
        if params:
            self.solr_params.update(params)
        if 'rows' not in self.solr_params:
            self.solr_params['rows'] = self.default_row_size
        return self.solr_params


    def _get_from_solr(self):
        results = self.solr_result_set['docs']
        self.reset_query()
        return results

    def re_search_required(self, compiled_query_string):
        result = compiled_query_string != self.solr_preceding_query or self.solr_params != self.solr_preceding_params
        self.solr_preceding_query = compiled_query_string
        self.solr_preceding_params = self.solr_params
        return result

    def _exec_query(self, **params):
        compiled_query_string = self._compile_query()
        if self.re_search_required(compiled_query_string):
            self.solr_result_set = self.bucket.search(compiled_query_string, self._cfg.index, **self._process_params(**params))
            self.refetch_required(True)
            # print "SOLR QUERY:", compiled_query_string
        else:
            self.refetch_required(False)
        return self
