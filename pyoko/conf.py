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
        self.SETTINGS_MODULE = os.environ.get('PYOKO_SETTINGS')
        self.MODELS_MODULE = '.'.join(self.SETTINGS_MODULE.split('.')[:1]) + '.models'

        try:
            mod = importlib.import_module(self.SETTINGS_MODULE)
        except ImportError as e:
            raise ImportError(
                "Could not import settings '%s' (Is it on sys.path? Is there an import error in the settings file?): %s"
                % (self.SETTINGS_MODULE, e)
            )

        self._explicit_settings = set()
        for setting in dir(mod):
            if setting.isupper():
                setting_value = getattr(mod, setting)
                setattr(self, setting, setting_value)


settings = Settings()
