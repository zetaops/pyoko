# -*-  coding: utf-8 -*-
"""
command line management interface
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.


import argparse
from importlib import import_module


class ManagementCommands(object):
    def __init__(self, args=None):
        self.report = ""
        self.robot = None
        if args:
            self.parse_args(args)
            getattr(self, self.args.command)()
        print(self.report)

    def parse_args(self, args):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(
            title='subcommands', description='valid subcommands',
            help='additional help')
        parser_create = subparsers.add_parser('update_schema')
        parser_create.set_defaults(command='schema_update')
        parser_create.add_argument(
            '--bucket', required=True, help='Bucket name(s) to be updated')

        parser_create = subparsers.add_parser('index_bucket')
        parser_create.set_defaults(command='index_bucket')
        parser_create.add_argument(
            '--bucket', required=True,
            help='Bucket name(s) to be indexed. (Comma separated)')
        self.args = parser.parse_args(args)

    def _get_models(self):
        import_module('tests.models')
        self.registry = import_module('pyoko.model')._registry

    def schema_update(self):
        self._get_models()
        from pyoko.db.schema_update import SchemaUpdater

        self.robot = SchemaUpdater(self.registry, self.args.bucket)
        self.robot.run()
        self.report = self.robot.create_report()


if __name__ == '__main__':
    import sys

    ManagementCommands(sys.argv[1:])
