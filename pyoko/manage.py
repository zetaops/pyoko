# -*-  coding: utf-8 -*-
"""
protoype of
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.


import argparse
from importlib import import_module
import sys



class ManagementCommands(object):

    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("command", help="possible commands: schema_update")
        self.args = parser.parse_args()
        getattr(self, self.args.command)()

    def get_models(self):
        import_module('models')
        self.registry = import_module('pyoko.model')._registry


    def schema_update(self):
        self.get_models()
        from pyoko.db.schema_update import SchemaUpdater
        su = SchemaUpdater(self.registry)
        su.run()

if __name__ == '__main__':

    ManagementCommands()

