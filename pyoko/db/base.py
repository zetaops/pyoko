# -*-  coding: utf-8 -*-
"""
this module contains a base class for other db access classes
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import copy

from enum import Enum
from pyoko.db.connection import http_client, riak

from pyoko.exceptions import MultipleObjectsReturned
from pyoko.lib.py2map import Dictomap
from pyoko.lib.utils import DotDict, grayed





# TODO: Add tests
# TODO: Add "ignore marked as _deleted"
# TODO: Add OR support



ReturnType = Enum('ReturnType', 'Solr Object Data Model')


class DBObjects(object):
    """
    This class implements Django-esque query APIs with the aim of fusing Solr and Riak in a more pythonic way
    """

    def __init__(self, **conf):

        self.bucket = riak.RiakBucket
        self._cfg = conf
        self._cfg['row_size'] = 1000
        if 'model' in self._cfg:
            self._cfg['rtype'] = ReturnType.Model
        else:
            self._cfg['rtype'] = ReturnType.Object
        self.__client = self._cfg.pop('client', http_client)
        self._data_type = None  # we convert new object data according to bucket datatype, eg: Dictomaping for 'map' type


        self._solr_query = {}  # query parts, will be compiled before execution
        self._solr_params = {}  # search parameters. eg: rows, fl, start, sort etc.
        self._solr_locked = False
        self._solr_cache = {}
        self._riak_cache = []  # caching riak result, for repeating iterations on same query

        self._new_record_value = None



    # ######## Development Methods  #########

    def w(self, brief=True):

        print grayed("results : ", len(self._solr_cache.get('docs', [])) if brief else self._solr_cache)
        print grayed("query : ", self._solr_query)
        print grayed("params : ", self._solr_params)
        print grayed("riak_cache : ", len(self._riak_cache) if brief else self._riak_cache)
        print grayed("return_type : ", self._cfg['rtype'])
        print grayed("new_value : ", self._new_record_value)
        print " "
        return self

    def _clear_bucket(self):
        """
        for development purposes, normally we should never delete anything, let alone the whole bucket!
        """
        if not 'yes' == raw_input("Say yes if you really want to delete all records in this bucket % s:" % self.bucket):
            return
        i = 0
        for pck in self.bucket.stream_keys():
            for k in pck:
                i += 1
                self.bucket.get(k).delete()
        return "%s record deleted" % i

    # ######## Python Magic  #########

    def __iter__(self):
        # print "ITER", self
        if not self._solr_cache and self._cfg['rtype'] in (ReturnType.Data, ReturnType.Object):
            self._params(fl='_yz_rk')
            # no need to fetch everything if we going to fetch from riak anyway
        self._exec_query()
        if self._cfg['rtype'] == ReturnType.Object:
            self._get_from_db()
        elif self._cfg['rtype'] == ReturnType.Data:
            self._get_data_from_db()
        return iter(self._riak_cache or self._solr_cache['docs'])


    def __len__(self):
        # self._exec_query()
        # print "THIS IS LEN"
        return self.count()

    def __getitem__(self, index):
        # print "THIS IS GETITEM"
        if isinstance(index, int):
            self._params(rows=1, start=index)
            return self._get()
        elif isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            clone = copy.deepcopy(self)
            clone._params(rows=stop - start, start=start)
            return clone
        else:
            raise TypeError("index must be int or slice")

    def __deepcopy__(self, memo=None):
        """
        A deep copy method that doesn't populate caches and shares same Riak client
        """
        obj = self.__class__()
        # print "COPY", obj, memo
        # print self.__dict__
        for k, v in self.__dict__.items():
            # print "copy", k, v
            if k == 'riak_cache':
                obj.__dict__[k] = []
            if k == '_solr_cache':
                obj.__dict__[k] = {}
            elif k.endswith(('bucket', '__client')):
                obj.__dict__[k] = v
            else:
                obj.__dict__[k] = copy.deepcopy(v, memo)
        return obj


    # ######## Riak Methods  #########

    def set_bucket(self, type, name):
        self._cfg['bucket_type'] = type
        self._cfg['bucket_name'] = name
        self.bucket = self.__client.bucket_type(self._cfg['bucket_type']).bucket(self._cfg['bucket_name'])
        if 'index' not in self._cfg:
            self._cfg.index = self._cfg['bucket_name']
        self._data_type = self.bucket.get_properties().get('datatype', None)
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

    def save(self, value=None, key=None):
        value = value or self._new_record_value
        if self._data_type == 'map' and isinstance(value, dict):
            return Dictomap(self.bucket, value, str(key)).map.store()
        else:
            return self.bucket.new(data=value, key=key).store()

    def _save_model(self):
        model = self._cfg['model']
        riak_object = self.save(model.clean_value(), model.key)
        if not model.key:
            model.key = riak_object.key

    def _get_from_db(self):
        """
        get objects from riak bucket
        :return: :class:`~riak.riak_object.RiakObject` or
                :class:`~riak.datatypes.Datatype`
        """
        if not self._riak_cache:
            if 'multiget' not in self._cfg:
                self._riak_cache = map(lambda k: self.bucket.get(k['_yz_rk']), self._solr_cache['docs'])
            else:
                self._riak_cache = self.bucket.multiget(keys=map(lambda k: k['_yz_rk'], self._solr_cache['docs']))


    def _get_data_from_db(self):
        """
        get json data from riak bucket
        :return: Json
        """
        if not self._riak_cache:
            if 'multiget' in self._cfg:
                self._riak_cache = map(lambda o: o.data, self.bucket.multiget(keys=
                    map(lambda k: k['_yz_rk'], self._solr_cache['docs'])))
            else:
                self._riak_cache = map(lambda k: self.bucket.get(k['_yz_rk']).data, self._solr_cache['docs'])

    def _get(self):
        self._exec_query()
        if not self._riak_cache and self._cfg['rtype'] in (ReturnType.Object, ReturnType.Data):
            self._riak_cache = [self.bucket.get(self._solr_cache['docs'][0]['_yz_rk'])]

        if self._cfg['rtype'] == ReturnType.Object:
            return self._riak_cache[0]
        elif self._cfg['rtype'] == ReturnType.Data:
            return self._riak_cache[0].data
        else:
            return self._solr_cache['docs'][0]

    # ######## Solr/Query Related Methods  #########

    def filter(self, **filters):
        # print "FILTER", self, filters
        clone = copy.deepcopy(self)
        clone.solr_query.update(filters.copy())
        return clone

    # def all(self):
    #     self.params(fl='_yz_rk')
    #     return self

    def get(self, key=None):
        if key:
            return self.bucket.get(key)
        else:
            self._exec_query()
            if self.count() > 1:
                raise MultipleObjectsReturned()
            return self._get()

    def count(self):
        if not self._solr_cache:
            self._params(rows=0)
            self._exec_query()
        return self._solr_cache.get('num_found', -1)

    def _params(self, **params):
        """
        add/update solr query parameters
        """
        assert not self._solr_locked, "Query already executed, no changes can be made."
        self._solr_params.update(params)


    def fields(self, *args):  # riak client needs _yz_rk to distinguish between old and new search API.
        self._solr_params.update({'fl': ' '.join(set(args + ('_yz_rk',)))})
        return self

    def solr(self):
        """
        returns raw solr result
        """
        clone = copy.deepcopy(self)
        clone.return_type = ReturnType.Solr
        return clone

    def data(self):
        """
        return data instead of riak object(s)
        """
        clone = copy.deepcopy(self)
        clone.return_type = ReturnType.Data
        return clone

    def _compile_query(self):
        """
        this will support "OR" and maybe other more advanced queries as well
        :return: Solr query string
        """
        # if not self.solr_query:
        # self.solr_query.add('*:*')  # get/count everything
        # elif len(self.solr_query) > 1 and '*:*' in self.solr_query:
        # self.solr_query.remove('*:*')
        query = []
        for key, val in self._solr_query.items():
            key = key.replace('__', '.')
            if val is None:
                key = '-%s' % key
                val = '[* TO *]'
            query.append("%s:%s" % (key, val))
        # if old != self.solr_query:
        # self.solr_query_updated = True
        anded = ' AND '.join(query)
        joined_query = anded
        return joined_query

    def _process_params(self):
        if 'rows' not in self._solr_params:
            self._solr_params['rows'] = self._cfg['row_size']
        return self._solr_params

    def _exec_query(self):
        if not self._solr_locked:
            self._solr_cache = self.bucket.search(self._compile_query(), self._cfg['index'], **self._process_params())
            self._solr_locked = True
        return self

