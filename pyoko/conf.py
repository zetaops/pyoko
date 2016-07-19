# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

import importlib
import os


class Settings(object):
    def __init__(self):
        """
        Proxy object for both static and dynamic app settings
        :return:
        """
        self.DEBUG = bool(os.environ.get('DEBUG'))
        self.DEBUG_LEVEL = int(os.environ.get('DEBUG_LEVEL', 0))
        self.SEARCH_INDEXES = {}
        self.CATALOG_DATA_MANAGER = "pyoko.lib.utils.simple_choices_manager"
        self.FILE_MANAGER = "pyoko.lib.utils.SimpleRiakFileManager"
        self.DATE_DEFAULT_FORMAT = ""
        self.DATETIME_DEFAULT_FORMAT = ""
        self.SETTINGS_MODULE = os.environ.get('PYOKO_SETTINGS')
        self.MODELS_MODULE = '.'.join(
            self.SETTINGS_MODULE.split('.')[:1]) + '.models'

        try:
            mod = importlib.import_module(self.SETTINGS_MODULE)
        except ImportError as e:
            raise ImportError(
                "Could not import settings '%s' (Is it on sys.path? "
                "Is there an import error in the settings file?): %s"
                % (self.SETTINGS_MODULE, e)
            )
        for setting in dir(mod):
            if setting.isupper():
                setting_value = getattr(mod, setting)
                setattr(self, setting, setting_value)
        if self.DEBUG:
            import sys
            # Will be used to store solr query logs
            sys._debug_db_queries = []

            # def get_index(self, bucket_name):
    #     """
    #     returns index name of given bucket (model)
    #     if index can not found in SEARCH_INDEX dict of settings instance
    #     we get up to date data from db and cache it for future requests
    #     :type bucket_name: str
    #     :return: index name
    #     """
    #     if not self.SEARCH_INDEXES:
    #         from pyoko.db.connection import client
    #         self.SEARCH_INDEXES = client.bucket('pyoko_settings').get(
    #             'search_indexes').data or {}
    #         if not self.SEARCH_INDEXES:
    #             self.update_index()
    #     try:
    #         return self.SEARCH_INDEXES[bucket_name]
    #     except KeyError:
    #         raise Exception("Error: No index found for %s" % bucket_name)
    #
    # def update_index(self, bucket_name=None, index_name=None):
    #     """
    #     Creates and updates search index cache
    #     (settings.SEARCH_INDEX[bucket_name: index_name])
    #      If bucket_name not given, updates all buckets,
    #      if index_name not given, gets it's value from riak
    #     :param bucket_name:
    #     :param index_name:
    #     """
    #     from pyoko.model import _registry
    #     from pyoko.db.connection import client
    #     pyoko_bucket_type = client.bucket_type(self.DEFAULT_BUCKET_TYPE)
    #     if not bucket_name:
    #         for model in _registry.registry:
    #             bucket = pyoko_bucket_type.bucket(model._get_bucket_name())
    #             self.SEARCH_INDEXES[bucket.name] = bucket.get_property(
    #                 'search_index')
    #     else:
    #         self.SEARCH_INDEXES[
    #             bucket_name] = index_name or pyoko_bucket_type.bucket(
    #             bucket_name).get_property('search_index')
    #     settings_bucket = client.bucket('pyoko_settings_%s' % self.DEFAULT_BUCKET_TYPE)
    #     search_indexes = settings_bucket.get('search_indexes')
    #     search_indexes.data = self.SEARCH_INDEXES
    #     search_indexes.store()


settings = Settings()
