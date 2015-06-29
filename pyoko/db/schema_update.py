# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import codecs
from pprint import pprint
from random import randint
from riak import RiakError
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

    FIELD_TEMPLATE = '<field type="{type}" name="{name}"  indexed="{index}" ' \
                     'stored="{store}" multiValued="{multi}" />'

    def __init__(self, registry, bucket_names):
        self.report = []
        self.registry = registry
        self.client = client
        self.bucket_names = [b.lower() for b in bucket_names.split(',')]


    def run(self):
        for klass in self.registry.get_base_models():
            if self.bucket_names[0] == 'all' or klass.__name__.lower() in self.bucket_names:
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
                                          type=field_type,
                                          index=str(index).lower(),
                                          store=str(store).lower(),
                                          multi=str(multi).lower())
                for name, field_type, index, store, multi in fields]

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
        riak doesn't support schema/index updates ( http://git.io/vLOTS )

        as a workaround, we create a temporary index,
        attach it to the bucket, delete the old index/schema,
        re-create the index with new schema, assign it to bucket,
        then delete the temporary index.

        :param byte new_schema: compiled schema
        :param str bucket_name: name of schema, index and bucket.
        :return: True or False
        :rtype: bool
        """
        bucket_type = self.client.bucket_type('models')
        bucket = bucket_type.bucket(bucket_name)

        # delete stale indexes
        # inuse_indexes = [b.get_properties().get('search_index') for b in
        #                  bucket_type.get_buckets()]
        # stale_indexes = [si['name'] for si in self.client.list_search_indexes()
        #                     if si['name'] not in inuse_indexes]
        # for stale_index in stale_indexes:
        #     self.client.delete_search_index(stale_index)

        # delete index of the bucket (if exist)
        existing_index = bucket.get_properties().get('search_index', None)
        if existing_index:
            tmp_index_name = "%s_%s" % (bucket_name, randint(1000, 9999))
            self.client.create_search_index(tmp_index_name)
            bucket.set_property('search_index', tmp_index_name)
            self.client.delete_search_index(existing_index)
            time.sleep(10)

        self.client.create_search_schema(bucket_name, new_schema)
        self.client.create_search_index(bucket_name, bucket_name)
        bucket.set_property('search_index', bucket_name)

        if existing_index:
            self.client.delete_search_index(tmp_index_name)

        schema_from_riak = self.client.get_search_schema(bucket_name)['content']
        return bucket.get_property('search_index') == bucket_name and \
               schema_from_riak == new_schema.decode("utf-8")

