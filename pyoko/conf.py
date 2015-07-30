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
        self.SEARCH_INDEXES = {}
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

    def get_index(self, bucket_name):
        if not self.SEARCH_INDEXES:
            from pyoko.db.connection import client
            self.SEARCH_INDEXES = client.bucket('pyoko_settings').get(
                'search_indexes').data
        try:
            return self.SEARCH_INDEXES[bucket_name]
        except KeyError:
            raise Exception("Error: No index found for %s" % bucket_name)

    def update_index(self, bucket_name=None, index_name=None):
        from pyoko.model import _registry
        from pyoko.db.connection import client
        pyoko_bucket_type = client.bucket_type(self.DEFAULT_BUCKET_TYPE)
        if not bucket_name:
            for bucket in pyoko_bucket_type.get_buckets():
                self.SEARCH_INDEXES[bucket.name] = bucket.get_property(
                    'search_index')
        else:
            self.SEARCH_INDEXES[
                bucket_name] = index_name or pyoko_bucket_type.bucket(
                bucket_name).get_property('search_index')
        settings_bucket = client.bucket('pyoko_settings')
        search_indexes = settings_bucket.get('search_indexes')
        search_indexes.data = self.SEARCH_INDEXES
        search_indexes.store()


settings = Settings()
