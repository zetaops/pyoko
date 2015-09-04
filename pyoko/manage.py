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
from six import add_metaclass


class CommandRegistry(type):
    registry  = {}

    @classmethod
    def add_command(cls, command_model):
        name = command_model.__name__
        if name not in cls.registry and name != 'Command':
            cls.registry[command_model.__name__] = command_model

    def __init__(mcs, name, bases, attrs):
        CommandRegistry.add_command(mcs)

    @classmethod
    def get_commands(cls):
        return cls.registry.values()


@add_metaclass(CommandRegistry)
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
        return updater.create_report()

class ManagementCommands(object):
    """
    all CLI commands executed by this class.

    You can add your own Command objects in your manage.py file:

    from pyoko.manage import Command
    class MyCmd(Command):
        CMD_NAME = 'mycommand'
        PARAMS = [('my_param', True, 'Example description')]

        def run(self):
            import os
            self.manager.report = os.popen('ls -lah').read()
    """
    def __init__(self, args=None):
        self.report = ""
        # self.commands = [SchemaUpdate]
        self.commands = CommandRegistry.get_commands()
        if args:
            input = args
        else:
            input = argv[1:]
        self.parse_args(input)
        print(self.args.command() or '\nProcess completed')


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
