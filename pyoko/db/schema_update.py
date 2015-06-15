# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import codecs
from pprint import pprint
import six
import time
from pyoko.db.connection import http_client as client
# from pyoko.db.solr_schema_fields import SOLR_FIELDS
import os, inspect
from pyoko.lib.utils import un_camel, random_word


class SchemaUpdater(object):
    """
    traverses trough all models, collects fields marked for index or store in solr
    then creates a solr schema for these fields.
    """

    FIELD_TEMPLATE = '<field type="{type}" name="{name}"  indexed="{index}" stored="{store}" multiValued="{multi}" />'

    def __init__(self, registry, bucket_names):
        self.report = []
        self.registry = registry
        self.client = client
        self.bucket_names = [b.lower() for  b in bucket_names.split(',')]


    def run(self):
        for klass in self.registry.get_base_models():
            if self.bucket_names[
                0] == 'all' or klass.__name__.lower() in self.bucket_names:
                ins = klass()
                fields = self.get_schema_fields(ins._collect_index_fields())
                new_schema = self.compile_schema(fields)
                bucket_name = ins._get_bucket_name()
                self.report.append((bucket_name, self.apply_schema(new_schema,
                                                                   bucket_name)))

    def create_report(self):
        """
        creates a text report for the human user
        :return: str
        """
        buckets, results = zip(*self.report)
        report = ''
        if all(results):
            report = "Schema and index definitions successfully applied for:\n + " + \
                     "\n + ".join(buckets)
        else:
            report = "Operation failed:\n" + str(self.report)
        return report

    @classmethod
    def get_schema_fields(cls, fields):
        """

        :param list[(,)] fields: field props tupple list
        :rtype: list[str]
        :return: schema fields list
        """
        return [cls.FIELD_TEMPLATE.format(name=name,
                                          type=(
                                          solr_type or field_type).lower(),
                                          index=str(index).lower(),
                                          store=str(store).lower(),
                                          multi=str(multi).lower())
                for name, field_type, solr_type, index, store, multi in fields]

    def compile_schema(self, fields):
        """
        joins schema fields with base solr schema

        :param list[str] fields: field list
        :return: compiled schema
        :rtype: byte
        """
        path = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        with codecs.open("%s/solr_schema_template.xml" % path, 'r',
                         'utf-8') as fh:
            schema_template = fh.read()
        return schema_template.format('\n'.join(fields)).encode('utf-8')

    def apply_schema(self, new_schema, bucket_name):
        """
        creates an index, schema and a bucket for the given data
        :param byte new_schema: compiled schema
        :param str bucket_name: name of schema, index and bucket.
        :return: True or False
        :rtype: bool
        """
        schema_name = "%s_%s" % (bucket_name, time.time())
        self.client.create_search_schema(schema_name, new_schema)
        self.client.create_search_index(schema_name, schema_name)
        # self.client.
        # with self.client._transport() as t:
        #     t._request('PUT', t.search_index_path('student'),
        # {'content-type': 'text/plain'}, 'RELOAD')
        b = self.client.bucket_type('models').bucket(bucket_name)
        b.set_property('search_index', schema_name)

        schema_from_riak = self.client.get_search_schema(
            schema_name)['content']
        return b.get_property('search_index') == schema_name and \
               schema_from_riak == new_schema.decode("utf-8")

    def re_index(self):
        """
        re-stores all records for re-indexing
        :return: re-indexed record count
        :rtype: int
        """
        i = 0
        for bucket_name in self.bucket_names:
            b = self.client.bucket_type('models').bucket(bucket_name)
            for keys in b.stream_keys():
                for key in keys:
                    i += 1
                    obj = b.get(key)
                    obj.store()
        return i
