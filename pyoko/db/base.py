# -*-  coding: utf-8 -*-
"""
this module contains a base class for other db access classes
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import copy

# noinspection PyCompatibility
from enum import Enum
from pyoko.conf import settings
from pyoko.db.connection import client
import riak
from pyoko.exceptions import MultipleObjectsReturned
from pyoko.lib.py2map import Dictomap
from pyoko.lib.utils import grayed

# TODO: Add "ignore marked as _deleted"
# TODO: Add OR support



ReturnType = Enum('ReturnType', 'Solr Object Model')


# noinspection PyTypeChecker
class DBObjects(object):
    """
    Data access layer for Solr/Riak
    """

    def __init__(self, **conf):

        self.bucket = riak.RiakBucket
        self._cfg={'row_size': 100,
                   'rtype': ReturnType.Model}
        self._cfg.update(conf)
        self.model = None
        self._client = self._cfg.pop('client', client)
        if 'model' in conf:
            self.model = conf['model']
            self.model_class = self.model.__class__
        elif 'model_class' in conf:
            self.model_class = conf['model_class']

        self.set_bucket(self.model_class._META['bucket_type'],
                        self.model_class._get_bucket_name())
        self._data_type = None  # we convert new object data according to
        # bucket datatype, eg: Dictomaping for 'map' type
        self.compiled_query = ''
        self._solr_query = {}  # query parts, will be compiled before execution
        self._solr_params = {}  # search parameters. eg: rows, fl, start, sort etc.
        self._solr_locked = False
        self._solr_cache = {}
        self._riak_cache = []  # caching riak result,
        # for repeating iterations on same query

    # ######## Development Methods  #########

    def w(self, brief=True):
        """
        can be called at any time on query chaining.
        prints debug information for current state of the dbobject
        eg: list(Student.objects.w().filter(name="Jack").w())
        :param bool brief: instead of whole content, only print length of the caches
        :return:
        """
        print(grayed("results : ", len(
            self._solr_cache.get('docs', [])) if brief else self._solr_cache))
        print(grayed("query : ", self._solr_query))
        print(grayed("params : ", self._solr_params))
        print(grayed("riak_cache : ",
                     len(self._riak_cache) if brief else self._riak_cache))
        print(grayed("return_type : ", self._cfg['rtype']))
        print(" ")
        return self

    def _clear_bucket(self):
        """
        only for development purposes
        """
        i = 0
        for k in self.bucket.get_keys():
            i += 1
            self.bucket.get(k).delete()
        return i

    def _count_bucket(self):
        """
        only for development purposes
        counts number of objects in the bucket.
        :return:
        """
        return sum([len(key_list) for key_list in self.bucket.stream_keys()])

    # ######## Python Magic  #########

    def __iter__(self):
        self._exec_query()
        for doc in self._solr_cache['docs']:
            if self._cfg['rtype'] == ReturnType.Solr:
                yield doc
            else:
                riak_obj = self.bucket.get(doc['_yz_rk'])
                yield (self._make_model(riak_obj.data, riak_obj)
                       if self._cfg['rtype'] == ReturnType.Model else riak_obj)


    def __len__(self):
        # print("~~~~!!! __len__ CALLED !!!~~~~")
        return self.count()
        # return len(self._solr_cache)

    def __getitem__(self, index):
        if isinstance(index, int):
            self.set_params(rows=1, start=index)
            return self._get()
        elif isinstance(index, slice):
            # start, stop, step = index.indices(len(self))
            if index.start is not None:
                start = int(index.start)
            else:
                start = 0
            if index.stop is not None:
                stop = int(index.stop)
            else:
                stop = None
            if start >= 0 and stop:
                clone = copy.deepcopy(self)
                clone.set_params(rows=stop - start, start=start)
                return clone
            else:
                raise TypeError("unlimited slicing not supported")
        else:
            raise TypeError("index must be int or slice")

    def __deepcopy__(self, memo=None):
        """
        A deep copy method that doesn't populate caches
        and shares Riak client and bucket
        """
        obj = self.__class__(**self._cfg)
        # print "COPY", obj, memo
        # print self.__dict__
        for k, v in self.__dict__.items():
            if k == '_riak_cache':
                obj.__dict__[k] = []
            elif k == '_solr_cache':
                obj.__dict__[k] = {}
            elif k.endswith(('bucket', '_client', 'model', 'model_class')):
                obj.__dict__[k] = v
            else:
                obj.__dict__[k] = copy.deepcopy(v, memo)
        self.compiled_query = ''
        return obj

    def set_bucket(self, type, name):
        """
        prepares bucket, sets index name
        :param str type: bucket type
        :param str name: bucket name
        :return:
        """
        self._cfg['bucket_type'] = type
        self._cfg['bucket_name'] = name
        self.bucket = self._client.bucket_type(
            self._cfg['bucket_type']).bucket(self._cfg['bucket_name'])
        if 'index' not in self._cfg:
            self._cfg['index'] = "%s_%s" % (settings.DEFAULT_BUCKET_TYPE, name)
        return self

    def save(self, data, key=None):
        """
        saves data to riak with optional key.
        converts python dict to riak map if needed.
        :param dict data: data to be saved
        :param str key: riak object key
        :return:
        """
        # if self._data_type == 'map' and isinstance(data, dict):
        #     return Dictomap(self.bucket, data, str(key)).map.store()
        # else:
        if key is None:
            return self.bucket.new(data=data).store()
        else:
            obj = self.bucket.get(key)
            obj.data = data
            return obj.store()



    def save_model(self):
        """
        saves the model instance to riak
        :return:
        """
        riak_object = self.save(self.model.clean_value(), self.model.key)
        if not self.model.key:
            self.model.key = riak_object.key

    def _get(self):
        """
        executes solr query if needed then returns first object according to
        selected ReturnType (defaults to Model)
        :return: pyoko.Model or riak.Object or solr document
        """
        self._exec_query()
        if not self._riak_cache and self._cfg['rtype'] != ReturnType.Solr:
            self._riak_cache = [self.bucket.get(
                self._solr_cache['docs'][0]['_yz_rk'])]

        if self._cfg['rtype'] == ReturnType.Model:
            return self._make_model(self._riak_cache[0].data, self._riak_cache[0])
        elif self._cfg['rtype'] == ReturnType.Object:
            return self._riak_cache[0]
        else:
            return self._solr_cache['docs'][0]

    def _make_model(self, data, riak_obj=None):
        """
        creates a model instance with the given data
        :param dict data: model data returned from db (riak or redis)
        :return: pyoko.Model
        """
        model = self.model_class()
        model.key = riak_obj.key if riak_obj else data.get('key')
        return model.set_data(data, from_db=True)


    def __repr__(self):
        return [obj for obj in self[:10]].__repr__()

    def filter(self, **filters):
        """
        applies query filters to queryset.
        :param dict filters: query  filter parameters filter(email='a@a.co',...)
        :return: DBObjects
        """
        clone = copy.deepcopy(self)
        clone._solr_query.update(filters.copy())
        return clone

    def exclude(self, **filters):
        """
        applies query filters to exclude from queryset.
        reusing filter method
        :param dict filters: query  filter parameters filter(email='a@a.co',...)
        :return: self.filter() with '-' with keys of filters
        """
        exclude = {'-%s' % key: value for key, value in filters.items()}
        return self.filter(**exclude)

    def get(self, key=None):
        """
        if key param exists, retrieves object from riak,
        otherwise ensures that we got only one doc from solr query
        :type key: builtins.NoneType
        :rtype: pyoko.Model
        """
        clone = copy.deepcopy(self)
        if key:
            clone._riak_cache = [self.bucket.get(key)]
        else:
            clone._exec_query()
            if clone.count() > 1:
                raise MultipleObjectsReturned()
        return clone._get()

    def count(self):
        """
        counts by executing solr query with rows=0 parameter
        :return:  number of objects matches to the query
        :rtype: int
        """

        if self._solr_cache:
            obj = self
        else:
            obj = copy.deepcopy(self)
            obj.set_params(rows=0)
            obj._exec_query()
        obj._exec_query()
        return obj._solr_cache.get('num_found', -1)

    def set_params(self, **params):
        """
        add/update solr query parameters
        """
        assert not self._solr_locked, "Query already executed, no changes can be made."
        self._solr_params.update(params)

    def fields(self, *args):
        """
        Riak's  official Python client (as of v2.1) depends on existence of "_yz_rk"
        for distinguishing between old and new search API.
        :param args:
        :return:
        """
        self._solr_params.update({'fl': ' '.join(set(args + ('_yz_rk',)))})
        return self

    def _set_return_type(self, type):
        self._cfg['rtype'] = type

    def solr(self):
        """
        set return type for raw solr docs
        """
        clone = copy.deepcopy(self)
        clone._set_return_type(ReturnType.Solr)
        return clone

    def data(self):
        """
        set return type as riak objects instead of pyoko models
        """
        clone = copy.deepcopy(self)
        clone._set_return_type(ReturnType.Object)
        return clone

    def raw(self, query, params=None):
        """
        make a raw query
        :param str query: solr query
        :param dict params: solr parameters
        """
        clone = copy.deepcopy(self)
        clone.compiled_query = query
        if params is not None:
            clone._solr_params = params
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
        if joined_query == '':
            joined_query = '*:*'
        self.compiled_query = joined_query

    def _process_params(self):
        if 'rows' not in self._solr_params:
            self._solr_params['rows'] = self._cfg['row_size']
        return self._solr_params

    def _exec_query(self):
        """
        executes solr query if it hasn't already executed.
        :return:
        """
        if not self._solr_cache and self._cfg['rtype'] != ReturnType.Solr:
            self.set_params(fl='_yz_rk')  # we're going to riak, fetch only keys
        if not self._solr_locked:
            if not self.compiled_query:
                self._compile_query()
            self._solr_cache = self.bucket.search(self.compiled_query,
                                                  self._cfg['index'],
                                                  **self._process_params())
            self._solr_locked = True
        return self
