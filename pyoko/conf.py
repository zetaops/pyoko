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

        self.SOLR = {
            'store': False,

        }

settings = Settings()
