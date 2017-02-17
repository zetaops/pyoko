# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

from __future__ import print_function
import codecs
from random import randint
from sys import stdout
import threading
import time
from riak import ConflictError, RiakError
from pyoko.conf import settings
from pyoko.db.connection import client, log_bucket
import os, inspect
import copy
from pyoko.manage import BaseThreadedCommand
from pyoko.manage import ReIndex

try:
    from urllib.request import urlopen
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import urlopen, HTTPError


class FakeContext(object):
    def has_permission(self, perm):
        return True


fake_context = FakeContext()


def wait_for_schema_creation(index_name):
    url = 'http://%s:8093/internal_solr/%s/select' % (settings.RIAK_SERVER, index_name)
    print("pinging solr schema: %s" % url, end='')
    while True:
        try:
            urlopen(url)
            return
        except HTTPError as e:
            if e.code == 404:
                time.sleep(1)
                import traceback
                print(traceback.format_exc())
            else:
                raise


def wait_for_schema_deletion(index_name):
    url = 'http://%s:8093/internal_solr/%s/select' % (settings.RIAK_SERVER, index_name)
    i = 0
    while True:
        i += 1
        stdout.write("\r Waiting for actual deletion of solr schema %s %s" % (index_name, i * '.'))
        stdout.flush()
        try:
            urlopen(url)
            time.sleep(1)
        except HTTPError as e:
            print("")
            if e.code == 404:
                return
            else:
                raise


def get_schema_from_solr(index_name):
    url = 'http://%s:8093/internal_solr/%s/admin/file?file=%s.xml' % (settings.RIAK_SERVER,
                                                                      index_name, index_name)
    try:
        return urlopen(url).read()
    except HTTPError as e:
        if e.code == 404:
            return ""
        else:
            raise


class SchemaUpdater(object):
    """
    traverses trough all models, collects fields marked for index or store in solr
    then creates a solr schema for these fields.
    """

    FIELD_TEMPLATE = '<field    type="{type}" name="{name}"  indexed="{index}" ' \
                     'stored="{store}" multiValued="{multi}" />'

    def __init__(self, models, threads, force):
        self.report = []
        self.models = models
        self.force = force
        self.client = client
        self.threads = int(threads)
        self.n_val = client.bucket_type(settings.DEFAULT_BUCKET_TYPE).get_property('n_val')
        self.base_thread = BaseThreadedCommand()

    def run(self, check_only=False):
        """

        Args:
            check_only:  do not migrate, only report migration is needed or not if True

        Returns:

        """
        reindex = ReIndex().reindex_model
        models = copy.deepcopy(self.models)
        num_models = len(models)
        self.client.create_search_index('foo_index', '_yz_default', n_val=self.n_val)

        print("Schema creation started for %s model(s) with max %s threads\n" % (
            num_models, self.threads))

        exec_models = []
        self.base_thread.do_with_submit(self.find_models_and_delete_search_index, models,
                                        self.force, exec_models, check_only,
                                        threads=self.threads)

        if exec_models:
            models = copy.deepcopy(exec_models)
            self.creating_schema_and_index(models, self.create_schema)
            self.creating_schema_and_index(models, self.create_index)
            self.base_thread.do_with_submit(reindex, models, threads=self.threads)

    def find_models_and_delete_search_index(self, model, force, exec_models, check_only):
        """
        Finds models to execute and these models' exist search indexes are deleted.
        For other operations, necessary models are gathered to list(exec_models)

        Args:
            model: model to execute
            force(bool): True or False if True, all given models are executed.
            exec_models(list): if not force, models to execute are gathered to list.
            If there is not necessity to migrate operation model doesn't put to exec list.
            check_only: do not migrate, only report migration is needed or not if True

        Returns:

        """
        ins = model(fake_context)
        fields = self.get_schema_fields(ins._collect_index_fields())
        new_schema = self.compile_schema(fields)
        bucket_name = model._get_bucket_name()
        bucket_type = client.bucket_type(settings.DEFAULT_BUCKET_TYPE)
        bucket = bucket_type.bucket(bucket_name)
        index_name = "%s_%s" % (settings.DEFAULT_BUCKET_TYPE, bucket_name)
        if not force:
            try:
                schema = get_schema_from_solr(index_name)
                if schema == new_schema:
                    print("Schema %s is already up to date, nothing to do!" % index_name)
                    return
                elif check_only and schema != new_schema:
                    print("Schema %s is not up to date, migrate this model!" % index_name)
                    return
            except:
                import traceback
                traceback.print_exc()
        bucket.set_property('search_index', 'foo_index')
        try:
            client.delete_search_index(index_name)
        except RiakError as e:
            if 'notfound' != e.value:
                raise
        wait_for_schema_deletion(index_name)
        exec_models.append(model)

    def creating_schema_and_index(self, models, func):
        """
        Executes given functions with given models.

        Args:
            models: models to execute
            func: function name to execute

        Returns:

        """
        waiting_models = []
        self.base_thread.do_with_submit(func, models, waiting_models, threads=self.threads)
        if waiting_models:
            print("WAITING MODELS ARE CHECKING...")
            self.creating_schema_and_index(waiting_models, func)

    def create_schema(self, model, waiting_models):
        """
        Creates search schemas.

        Args:
            model: model to execute
            waiting_models: if riak can't return response immediately, model is taken to queue.
            After first execution session, method is executed with waiting models and controlled.
            And be ensured that all given models are executed properly.

        Returns:

        """
        bucket_name = model._get_bucket_name()
        index_name = "%s_%s" % (settings.DEFAULT_BUCKET_TYPE, bucket_name)
        ins = model(fake_context)
        fields = self.get_schema_fields(ins._collect_index_fields())
        new_schema = self.compile_schema(fields)
        schema = get_schema_from_solr(index_name)
        if not (schema == new_schema):
            try:
                client.create_search_schema(index_name, new_schema)
                print("+ %s (%s) search schema is created." % (model.__name__, index_name))
            except:
                print("+ %s (%s) search schema checking operation is taken to queue." % (
                    model.__name__, index_name))
                waiting_models.append(model)

    def create_index(self, model, waiting_models):
        """
        Creates search indexes.

        Args:
            model: model to execute
            waiting_models: if riak can't return response immediately, model is taken to queue.
            After first execution session, method is executed with waiting models and controlled.
            And be ensured that all given models are executed properly.

        Returns:

        """
        bucket_name = model._get_bucket_name()
        bucket_type = client.bucket_type(settings.DEFAULT_BUCKET_TYPE)
        index_name = "%s_%s" % (settings.DEFAULT_BUCKET_TYPE, bucket_name)
        bucket = bucket_type.bucket(bucket_name)
        try:
            client.get_search_index(index_name)
            if not (bucket.get_property('search_index') == index_name):
                bucket.set_property('search_index', index_name)
                print("+ %s (%s) search index is created." % (model.__name__, index_name))
        except RiakError:
            try:
                client.create_search_index(index_name, index_name, self.n_val)
                bucket.set_property('search_index', index_name)
                print("+ %s (%s) search index is created." % (model.__name__, index_name))
            except RiakError:
                print("+ %s (%s) search index checking operation is taken to queue." % (
                model.__name__, index_name))
                waiting_models.append(model)

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

    @staticmethod
    def compile_schema(fields):
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