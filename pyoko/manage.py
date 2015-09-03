# -*-  coding: utf-8 -*-
"""
command line management interface
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.


from os import environ
from sys import argv

class Command(object):
    # name of your command
    # CMD_NAME = ''
    # parameters, can be accessed from self.manager.args
    # PARAMS = [(param_name, is_required, description),...]

    def __init__(self, manager):
        self.manager = manager

    def run(self):
        raise NotImplemented("You should override this method in your command class")

class SchemaUpdate(Command):
    CMD_NAME = 'update_schema'
    PARAMS = [('bucket', True, 'Bucket name(s) to be updated'),
              ('silent', False, 'Silent operation')]

    def run(self):
        from pyoko.db.schema_update import SchemaUpdater
        from pyoko.conf import settings
        from importlib import import_module
        import_module(settings.MODELS_MODULE)
        registry = import_module('pyoko.model').model_registry
        updater = SchemaUpdater(registry, self.manager.args.bucket, self.manager.args.silent)
        updater.run()
        self.manager.report = updater.create_report()

class ManagementCommands(object):
    """
    all CLI commands executed by this class.

    You can add your own Command objects in your manage.py file:

    myapp/manage.py:

        from pyoko.manage import *

        class MyCmd(Command):
            CMD_NAME = 'mycommand'
            PARAMS = [('my_param', True, 'Example description')]

            def run(self):
                import os
                self.manager.report = os.popen('ls -lah').read()

        environ.setdefault('PYOKO_SETTINGS', 'myapp.settings')

        ManagementCommands(argv[1:], commands=[MyCmd])

    """
    def __init__(self, args=None, commands=None):
        self.report = ""
        self.commands = [SchemaUpdate]
        if commands:
            self.commands.extend(commands)
        if args:
            self.parse_args(args)
            self.args.command()
        print(self.report)

    def parse_args(self, args):
        import argparse
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(title='subcommands',
                                           description='valid subcommands',
                                           help='additional help')
        for cmd_class in self.commands:
            cmd = cmd_class(self)
            parser_create = subparsers.add_parser(cmd.CMD_NAME)
            parser_create.set_defaults(command=cmd.run)
            if hasattr(cmd, 'PARAMS'):
                for param, required, help in cmd.PARAMS:
                    parser_create.add_argument('--%s' % param, required=required, help=help)
        self.args = parser.parse_args(args)
