# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

import codecs
from random import randint
import threading
import time
from pyoko.conf import settings
from pyoko.db.connection import client
import os, inspect
from pyoko.lib.utils import un_camel, random_word


class FakeContext(object):
    def has_permission(self, perm):
        return True


fake_context = FakeContext()


def wait_for_schema_creation(index_name):
    import urllib2
    while True:
        url = 'http://%s:8093/internal_solr/%s/select' % (settings.RIAK_SERVER, index_name)
        print("pinging solr schema: %s" % url)
        try:
            urllib2.urlopen(url)
            return
        except urllib2.HTTPError, e:
            if e.code == 404:
                time.sleep(1)
                import traceback
                print(traceback.format_exc())
            else:
                raise

def wait_for_schema_deletion(index_name):
    import urllib2
    while True:
        url = 'http://%s:8093/internal_solr/%s/select' % (settings.RIAK_SERVER, index_name)
        print("pinging solr schema: %s" % url)
        try:
            urllib2.urlopen(url)
            time.sleep(1)
        except urllib2.HTTPError, e:
            if e.code == 404:
                return
            else:
                raise

class SchemaUpdater(object):
    """
    traverses trough all models, collects fields marked for index or store in solr
    then creates a solr schema for these fields.
    """

    FIELD_TEMPLATE = '<field type="{type}" name="{name}"  indexed="{index}" ' \
                     'stored="{store}" multiValued="{multi}" />'

    def __init__(self, registry, bucket_names, threads, reindex):
        self.report = []
        self.registry = registry
        self.reindex = reindex
        self.client = client
        self.threads = int(threads)
        self.bucket_names = [b.lower() for b in bucket_names.split(',')]
        self.t1 = 0.0  # start time

    def run(self):
        # TODO: Limit thread size to 10-20
        self.t1 = time.time()
        apply_threads = []
        models = [model for model in self.registry.get_base_models()
                  if self.bucket_names[0] == 'all' or
                  model.__name__.lower() in self.bucket_names]
        num_models = len(models)
        pack_size = num_models / self.threads or 1
        for i in range(0, num_models, pack_size):
            job_pack = []
            for model in models[i:i+pack_size]:
                ins = model(fake_context)
                fields = self.get_schema_fields(ins._collect_index_fields())
                new_schema = self.compile_schema(fields)
                job_pack.append((new_schema, model))
            apply_threads.append(
                threading.Thread(target=self.apply_schema, args=(self.client,
                                                                 self.reindex,
                                                                 job_pack)))

        print("Schema creation started for %s model(s) with %s threads\n" % (
            num_models, self.threads))
        for t in apply_threads:
            t.start()
        for t in apply_threads:
            t.join()
        if apply_threads:
            self.report = "\nSchema and index definitions successfully " \
                          "applied for the models listed above."

    def create_report(self):
        """
        creates a text report for the human user
        :return: str
        """

        if self.report:
            self.report += "\n Operation took %s secs" % round(
                time.time() - self.t1)
        else:
            self.report = "Operation failed: %s \n" % self.report
        return self.report

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
        path = os.path.dirname(os.path.realpath(__file__))
        # path = os.path.dirname(
        #     os.path.abspath(inspect.getfile(inspect.currentframe())))
        with codecs.open("%s/solr_schema_template.xml" % path, 'r', 'utf-8') as fh:
            schema_template = fh.read()
        return schema_template.format('\n'.join(fields)).encode('utf-8')



    @staticmethod
    def apply_schema(client, reindex, job_pack):
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
        for new_schema, model in job_pack:
            try:
                bucket_name = model._get_bucket_name()
                bucket_type = client.bucket_type(settings.DEFAULT_BUCKET_TYPE)
                bucket = bucket_type.bucket(bucket_name)
                n_val = bucket_type.get_property('n_val')
                # delete stale indexes
                # inuse_indexes = [b.get_properties().get('search_index') for b in
                #                  bucket_type.get_buckets()]
                # stale_indexes = [si['name'] for si in self.client.list_search_indexes()
                #                     if si['name'] not in inuse_indexes]
                # for stale_index in stale_indexes:
                #     self.client.delete_search_index(stale_index)

                # suffix = 9000000000 - int(time.time())
                index_name = "%s_%s" % (settings.DEFAULT_BUCKET_TYPE, bucket_name)
                client.delete_search_index(index_name)
                wait_for_schema_deletion(index_name)
                client.create_search_schema(index_name, new_schema)
                client.create_search_index(index_name, index_name, n_val)
                bucket.set_property('search_index', index_name)
                print("+ %s (%s)" % (model.__name__, index_name))
                stream = bucket.stream_keys()
                i = 0
                for key_list in stream:
                    for key in key_list:
                        i += 1
                        bucket.get(key).store()
                stream.close()
                print("Re-indexed %s records of %s" % (i, bucket_name))

            except:
                # import traceback
                # print(traceback.format_exc())
                print("n_val: %s" % n_val)
                print("bucket_name: %s" % bucket_name)
                print("bucket_type: %s" % bucket_type)
                raise
