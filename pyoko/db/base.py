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
import json
from datetime import date
import time
from datetime import datetime

from riak.util import bytes_to_str

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

from enum import Enum
import six
from pyoko.conf import settings
from pyoko.db.connection import client
import riak
from pyoko.exceptions import MultipleObjectsReturned, ObjectDoesNotExist, PyokoError
from ..fields import DATE_FORMAT, DATE_TIME_FORMAT
# from pyoko.lib.py2map import Dictomap
from pyoko.lib.utils import grayed
import traceback
# TODO: Add OR support

import sys

ReturnType = Enum('ReturnType', 'Solr Object Model')


# noinspection PyTypeChecker
class DBObjects(object):
    """
    Data access layer for Solr/Riak
    """

    def __init__(self, **conf):
        self.current_context = None
        self._pass_perm_checks = False
        self.bucket = riak.RiakBucket
        self._cfg = {'row_size': 1000,
                     'rtype': ReturnType.Model}
        self._cfg.update(conf)
        self.model = None
        self._client = self._cfg.pop('client', client)
        self.index_name = ''
        if 'model' in conf:
            self.set_model(model=conf['model'])
        elif 'model_class' in conf:
            self.set_model(model_class=conf['model_class'])

        self.set_bucket(self.model_class.Meta.bucket_type,
                        self.model_class._get_bucket_name())
        self._data_type = None  # we convert new object data according to
        # bucket datatype, eg: Dictomaping for 'map' type
        self.compiled_query = ''
        # self._solr_query = {}  # query parts, will be compiled before execution
        self._solr_query = []  # query parts, will be compiled before execution
        self._solr_params = {
            'sort': 'timestamp desc'}  # search parameters. eg: rows, fl, start, sort etc.
        self._solr_locked = False
        self._solr_cache = {}
        self.key = None
        self._riak_cache = []  # caching riak result,
        # for repeating iterations on same query

    # ######## Development Methods  #########

    def set_model(self, model=None, model_class=None):
        if model:
            self.model = model
            self.model_class = model.__class__
            self.current_context = self.model.context
        elif model_class:
            self.model = None
            self.model_class = model_class
            self.current_context = None
        else:
            raise Exception("DBObjects should be called with a model instance or class")

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

    def distinct_values_of(self, field):
        # FIXME: Add support for query filters
        url = 'http://%s:8093/internal_solr/%s/select?q=-deleted%%3ATrue&wt=json&facet=true&facet.field=%s' % (
            settings.RIAK_SERVER, self.index_name, field)
        result = json.loads(bytes_to_str(urlopen(url).read()))
        dct = {}
        fresult = result['facet_counts']['facet_fields'][field]
        for i in range(0, len(fresult), 2):
            if i == len(fresult) - 1:
                break
            if fresult[i + 1]:
                dct[fresult[i]] = fresult[i + 1]
        return dct

    def _clear_bucket(self):
        """
        only for development purposes
        """
        i = 0
        for k in self.bucket.get_keys():
            i += 1
            self.bucket.get(k).delete()
        return i

    # def _count_bucket(self):
    #     """
    #     only for development purposes
    #     counts number of objects in the bucket.
    #     :return:
    #     """
    #     return sum([len(key_list) for key_list in self.bucket.stream_keys()])

    # ######## Python Magic  #########

    def __iter__(self):
        self._exec_query()
        for doc in self._solr_cache['docs']:
            if self._cfg['rtype'] == ReturnType.Solr:
                yield doc
            else:
                if settings.DEBUG:
                    t1 = time.time()
                riak_obj = self.bucket.get(doc['_yz_rk'])
                if settings.DEBUG:
                    sys._debug_db_queries.append({
                        'TIMESTAMP': t1,
                        'KEY': doc['_yz_rk'],
                        'BUCKET': self.index_name,
                        'TIME': round(time.time() - t1, 5)})
                if not riak_obj.data:
                    # # TODO: remove this, if not occur on production
                    # raise riak.RiakError("Empty object returned. "
                    #                 "Possibly a Riak-Solr sync delay issue.")
                    continue
                yield (self._make_model(riak_obj.data, riak_obj)
                       if self._cfg['rtype'] == ReturnType.Model else riak_obj)

    def __len__(self):
        return self.count()
        # return len(self._solr_cache)

    def __getitem__(self, index):
        if isinstance(index, int):
            return self.set_params(rows=1, start=index)._get()
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
        for k, v in self.__dict__.items():
            if k == '_riak_cache':
                obj.__dict__[k] = []
            elif k == '_solr_cache':
                obj.__dict__[k] = {}
            elif k == '_solr_query':
                obj.__dict__[k] = v[:]
            elif k.endswith(('current_context', 'bucket', '_client', 'model', 'model_class')):
                obj.__dict__[k] = v
            else:
                obj.__dict__[k] = copy.deepcopy(v, memo)
        obj.compiled_query = ''
        obj.key = None
        return obj

    def set_bucket(self, type, name):
        """
        prepares bucket, sets index name
        :param str type: bucket type
        :param str name: bucket name
        :return:
        """
        if type:
            self._cfg['bucket_type'] = type
        if name:
            self._cfg['bucket_name'] = name
        self.bucket = self._client.bucket_type(self._cfg['bucket_type']
                                               ).bucket(self._cfg['bucket_name'])
        self.index_name = "%s_%s" % (self._cfg['bucket_type'], self._cfg['bucket_name'])
        return self


    def save_model(self, model=None):
        """
        saves the model instance to riak
        :return:
        """
        # if model:
        #     self.model = model
        if settings.DEBUG:
            t1 = time.time()
        clean_value = model.clean_value()
        model._data = clean_value
        if settings.DEBUG:
            t2 = time.time()
        if not model.is_in_db():
            obj = self.bucket.new(data=clean_value).store()
            model.key = obj.key
            new_obj = True
        else:
            new_obj = False
            obj = self.bucket.get(model.key)
            obj.data = clean_value
            obj.store()
        if settings.DEBUG:
            sys._debug_db_queries.append({
                'TIMESTAMP': t1,
                'KEY': obj.key,
                'BUCKET': self.index_name,
                'SAVE_IS_NEW': new_obj,
                'SERIALIZATION_TIME': round(t2 - t1, 5),
                'TIME': round(time.time() - t2, 5)
            })
        return model

    def _get(self):
        """
        executes solr query if needed then returns first object according to
        selected ReturnType (defaults to Model)
        :return: pyoko.Model or riak.Object or solr document
        """
        if not self._riak_cache:
            self._exec_query()
        if not self._riak_cache and self._cfg['rtype'] != ReturnType.Solr:
            if not self._solr_cache['docs']:
                raise ObjectDoesNotExist("%s %s" % (self.index_name, self.compiled_query))
            if settings.DEBUG:
                t1 = time.time()
            self._riak_cache = [self.bucket.get(self._solr_cache['docs'][0]['_yz_rk'])]
            if settings.DEBUG:
                sys._debug_db_queries.append({
                    'TIMESTAMP': t1,
                    'KEY': self._solr_cache['docs'][0]['_yz_rk'],
                    'BUCKET': self.index_name,
                    'TIME': round(time.time() - t1, 5)})
        if self._cfg['rtype'] == ReturnType.Model:
            if not self._riak_cache[0].exists:
                raise ObjectDoesNotExist("%s %s" % (self.index_name,
                                                    self._riak_cache[0].key))
            return self._make_model(self._riak_cache[0].data,
                                    self._riak_cache[0])
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
        if not data:
            raise Exception("No data returned from Riak\n" + self._get_debug_data())
        model = self.model_class(self.current_context, _pass_perm_checks=self._pass_perm_checks)
        model.key = riak_obj.key if riak_obj else data.get('key')
        return model.set_data(data, from_db=True)

    def __repr__(self):
        try:
            # return "%s | %s | %s " % (self.model_class.__name__,
            #                           self._solr_query,
            #                           self._solr_params)
            return [obj for obj in self[:10]].__repr__()
        except AssertionError as e:
            return e.msg
        except TypeError:
            raise
            return str("queryset: %s" % self._solr_query)

    def _add_query(self, filters):
        # for f in filters:
        #     if len(f) == 2:
        #         f.append(False)  # mark as not escaped
        self._solr_query.extend([f if len(f) == 3 else (f[0], f[1], False) for f in filters])

    def filter(self, **filters):
        """
        applies query filters to queryset.
        :param dict filters: query  filter parameters filter(email='a@a.co',...)
        :return: DBObjects
        """
        clone = copy.deepcopy(self)
        clone._add_query(filters.items())
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

    def get_or_create(self, defaults=None, **kwargs):
        """
        Looks up an object with the given kwargs, creating one if necessary.
        Returns a tuple of (object, created), where created is a boolean
        specifying whether an object was created.
        """
        clone = copy.deepcopy(self)
        existing = list(clone.filter(**kwargs))
        count = len(existing)
        if count:
            if count > 1:
                raise MultipleObjectsReturned(
                        "%s objects returned for %s" % (count,
                                                        self.model_class.__name__))
            return existing[0], False
        else:
            data = defaults or {}
            data.update(kwargs)
            return self.model_class(**data).save(), True

    def get(self, key=None, **kwargs):
        """
        if key param exists, retrieves object from riak,
        otherwise ensures that we got only one doc from solr query
        :type key: builtins.NoneType
        :rtype: pyoko.Model
        """
        clone = copy.deepcopy(self)
        if key:
            self.key = key
            if settings.DEBUG:
                t1 = time.time()
            clone._riak_cache = [self.bucket.get(key)]
            if settings.DEBUG:
                sys._debug_db_queries.append({
                    'TIMESTAMP': t1,
                    'KEY': key,
                    'BUCKET': self.index_name,
                    'TIME': round(time.time() - t1, 5)})
        elif kwargs:
            return clone.filter(**kwargs).get()
        else:
            clone._exec_query()
            if clone.count() > 1:
                raise MultipleObjectsReturned(
                        "%s objects returned for %s" % (clone.count(),
                                                        self.model_class.__name__))
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
        if self._solr_locked:
            raise Exception("Query already executed, no changes can be made."
                            "%s %s %s" % (self._solr_query, self._solr_params)
                            )
        clone = copy.deepcopy(self)
        clone._solr_params.update(params)
        return clone

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

    def raw(self, query, **params):
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

    def or_filter(self, **filters):
        """
        applies query filters to queryset with OR operator.
        :param dict filters: query  filter parameters filter(email='a@a.co',...)
        :return: DBObjects
        """
        clone = copy.deepcopy(self)
        clone._add_query([("OR_QRY", filters)])
        return clone

    def search_on(self, *fields, **query):
        """
        search for query on given fields,
        search type can be: exact, contains, startswith, endswith, range
        eg:
        .search_on('name, 'surname', contains='john')
        .search_on('name, 'surname', startswith='jo')

        :param fields: field list to be searched on
        :param query:  search query
        :return: DBObjects
        """
        clone = copy.deepcopy(self)
        search_type = list(query.keys())[0]
        parsed_query = self._parse_query_type(search_type, self._escape_query(query[search_type]))
        clone._add_query([("OR_QRY", dict([(f, parsed_query) for f in fields]), True)])
        return clone

    def _escape_query(self, query, escaped=False):
        if escaped:
            return query
        query = six.text_type(query)
        for e in ['+', '-', '&&', '||', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~', '*',
                  '?', ':', ' ']:
            query = query.replace(e, "\\%s" % e)
        return query

    def _parse_query_type(self, qtype, query):
        if qtype == 'range':
            start = query[0] or '*'
            end = query[1] or '*'
            query = '[%s TO %s]' % (start, end)
        else:
            query = query
            if qtype == 'exact':
                query = query
            elif qtype == 'contains':
                query = "*%s*" % query
            elif qtype == 'startswith':
                query =  "%s*" % query
            elif qtype == 'endswith':
                query = "%s*" % query
            elif qtype == 'lte':
                query = '[* TO %s]' % query
            elif qtype == 'gte':
                query = '[%s TO *]' % query
        return query

    def _parse_query_key(self, key, val):
        if key.endswith('__contains'):
            key = key[:-10]
            val = self._parse_query_type('contains', val)
        elif key.endswith('__range'):
            key = key[:-7]
            val = self._parse_query_type('range', val)
        elif key.endswith('__startswith'):
            key = key[:-12]
            val = self._parse_query_type('startswith', val)
        elif key.endswith('__endswith'):
            key = key[:-10]
            val = self._parse_query_type('endswith', val)
        # lower than or equal
        elif key.endswith('__lte'):
            key = key[:-5]
            val = self._parse_query_type('lte', val)
        # greater than or equal
        elif key.endswith('__gte'):
            key = key[:-5]
            val = self._parse_query_type('gte', val)
        return key, val


    def _compile_query(self):
        """
        this will support "OR" and maybe other more advanced queries as well
        :return: Solr query string
        """

        # https://wiki.apache.org/solr/SolrQuerySyntax
        # http://lucene.apache.org/core/2_9_4/queryparsersyntax.html
        # TODO: escape following chars: + - && || ! ( ) { } [ ] ^ " ~ * ? : \
        query = []
        want_deleted = False
        filtered_query = self.model_class.row_level_access(self.current_context, self)
        if filtered_query is not None:
            self._solr_query += filtered_query._solr_query
        # print(self._solr_query)
        for key, val, is_escaped in self._solr_query:
            print(key, val, is_escaped)
            # querying on a linked model by model instance
            # it should be a Model, not a Node!
            if hasattr(val, '_TYPE'):
                val = val.key
                key += "_id"
            elif isinstance(val, date):
                val = val.strftime(DATE_FORMAT)
            elif isinstance(val, datetime):
                val = val.strftime(DATE_TIME_FORMAT)
            # if it's not one of the expected objects, it should be a string
            elif key == 'OR_QRY':
                key = 'NOKEY'
                val = ' OR '.join(['%s:%s' % self._parse_query_key(k, self._escape_query(v, is_escaped)) for k, v in val.items()])
            elif key.endswith('__in'):
                key = key[:-4]
                val = ' OR '.join(['%s:%s' % (key, self._escape_query(v, is_escaped)) for v in val])
                key = 'NOKEY'
            elif val is None:
                key = ('-%s' % key).replace('--', '')
                val = '[* TO *]'
            else:
                val = self._escape_query(val, is_escaped)

            key, val = self._parse_query_key(key, val)
            # in (or) query

            # as long as not explicitly asked for,
            # we filter out records with deleted flag
            if key == 'deleted':
                want_deleted = True
            # filter out records that contain any value for this field

            # else:
            #     val = self._parse_query_type('exact', val)

            key = key.replace('__', '.')
            if key == 'NOKEY':
                query.append("(%s)" % val)
            else:
                query.append("%s:%s" % (key, val))

        if not want_deleted:
            query.append('-deleted:True')
        anded = ' AND '.join(query)
        joined_query = anded
        if joined_query == '':
            joined_query = '*:*'
        if settings.DEBUG == "QUERY_DEBUG":
            try:
                print("QRY => %s" % joined_query)
            except:
                pass
        self.compiled_query = joined_query

    def _process_params(self):
        if 'rows' not in self._solr_params:
            self._solr_params['rows'] = self._cfg['row_size']
        for key, val in self._solr_params.items():
            if isinstance(val, str):
                self._solr_params[key] = val.encode(encoding='UTF-8')
        return self._solr_params

    def _get_debug_data(self):
        return ("                      ~=QUERY DEBUG=~                              "
                + six.text_type({
            'QUERY': self.compiled_query,
            'BUCKET': self.index_name,
            'QUERY_PARAMS': self._solr_params}))

    def _exec_query(self):
        """
        executes solr query if it hasn't already executed.
        :return:
        """
        if not self._solr_cache and self._cfg['rtype'] != ReturnType.Solr:
            self.set_params(
                    fl='_yz_rk')  # we're going to riak, fetch only keys
        if not self._solr_locked:
            if not self.compiled_query:
                self._compile_query()
            try:
                solr_params = self._process_params()
                if settings.DEBUG:
                    t1 = time.time()
                self._solr_cache = self.bucket.search(self.compiled_query,
                                                      self.index_name,
                                                      **solr_params)
                if settings.DEBUG:
                    sys._debug_db_queries.append({
                        'TIMESTAMP': t1,
                        'QUERY': self.compiled_query,
                        'BUCKET': self.index_name,
                        'QUERY_PARAMS': solr_params,
                        'TIME': round(time.time() - t1, 4)})
            except riak.RiakError as err:
                err.value += self._get_debug_data()
                raise
            self._solr_locked = True
        return self
