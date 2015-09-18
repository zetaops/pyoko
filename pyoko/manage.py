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
    registry = {}

    @classmethod
    def add_command(cls, command_model):
        name = command_model.__name__
        if name != 'Command':
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
    CMD_NAME = 'migrate'
    PARAMS = [{'name': 'model', 'required': True, 'help': 'Models name(s) to be updated'
                                                         'Say "all" to update all models'},
              {'name': 'threads', 'default': 12, 'help': 'Number of threads. Default: 12'},
              {'name': 'reindex', 'action': 'store_true', 'help': 'Reindex all records'},
              ]
    HELP = 'Creates/Updates SOLR schemas for given model(s)'

    def run(self):
        from pyoko.db.schema_update import SchemaUpdater
        from pyoko.conf import settings
        from importlib import import_module
        import_module(settings.MODELS_MODULE)
        registry = import_module('pyoko.model').model_registry
        updater = SchemaUpdater(registry,
                                self.manager.args.model,
                                self.manager.args.threads,
                                self.manager.args.reindex,
                                )
        updater.run()
        return updater.create_report()


class FlushDB(Command):
    CMD_NAME = 'flush_model'
    HELP = 'REALLY DELETES the contents of buckets'
    PARAMS = [{'name': 'model','required': True,
               'help': 'Models name(s) to be cleared. Say "all" to clear all models'},
              ]

    def run(self):
        from pyoko.db.schema_update import SchemaUpdater
        from pyoko.conf import settings
        from importlib import import_module
        import_module(settings.MODELS_MODULE)
        registry = import_module('pyoko.model').model_registry
        model_name = self.manager.args.model
        if model_name != 'all':
            models = [registry.get_model(model_name)]
        else:
            models = registry.get_base_models()
        for mdl in models:
            num_of_records = mdl.objects._clear_bucket()
            print("%s records deleted from %s " % (num_of_records, mdl.__name__))


class ManagementCommands(object):
    """
    All CLI commands executed by this class.
    You can create your own commands by extending Command class
    """

    def __init__(self, args=None):
        self.report = ""
        # self.commands = [SchemaUpdate]
        self.commands = CommandRegistry.get_commands()
        if args:
            input = args
        else:
            input = argv[1:]
        if not input:
            input = ['-h']
        self.parse_args(input)
        print(self.args.command() or '\nProcess completed')

    def parse_args(self, args):
        import argparse
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(title='Possible commands')
        for cmd_class in self.commands:
            cmd = cmd_class(self)
            # print(cmd.CMD_NAME)
            sub_parser = subparsers.add_parser(cmd.CMD_NAME, help=getattr(cmd, 'HELP', None))
            sub_parser.set_defaults(command=cmd.run)
            if hasattr(cmd, 'PARAMS'):
                for params in cmd.PARAMS:
                    name = "--%s" % params.pop("name")
                    # params['des']
                    if 'action' not in params:
                        params['nargs'] = '?'
                    sub_parser.add_argument(name, **params)
        self.args = parser.parse_args(args)
