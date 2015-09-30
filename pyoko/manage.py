# -*-  coding: utf-8 -*-
"""
command line management interface
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import codecs
from collections import defaultdict
import json

from os import environ
from sys import argv, stdout
from six import add_metaclass
from pyoko.model import super_context


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
              {'name': 'threads', 'default': 1, 'help': 'Number of threads. Default: 1'},
              {'name': 'force', 'action': 'store_true', 'help': 'Force schema creation'},
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
                                self.manager.args.force,
                                )
        updater.run()
        return updater.create_report()


class FlushDB(Command):
    CMD_NAME = 'flush_model'
    HELP = 'REALLY DELETES the contents of buckets'
    PARAMS = [{'name': 'model', 'required': True,
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
            models = [registry.get_model(name) for name in model_name.split(',')]
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
        self.args.command()

    def parse_args(self, args):
        import argparse
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(title='Possible commands')
        for cmd_class in self.commands:
            cmd = cmd_class(self)
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


class DumpData(Command):
    CMD_NAME = 'dump_data'
    HELP = 'Dumps all data to stdout (as JSON), pipe them to a file.'
    PARAMS = [{'name': 'model', 'required': True,
               'help': 'Models name(s) to be dumped. Say "all" to dump all models'},
              {'name': 'pretty', 'action': 'store_true', 'help': 'Pretty print. '
                                                                 'Needs "--tree" flag to be set'},
              {'name': 'tree', 'action': 'store_true',
               'help': 'Write whole dump as a big JSON object. Since it uses much more memory then'
                       ' standard linear mode (where each line dumped as a separate JSON document)'
                       ', DO NOT USE on big DBs.'},
              {'name': 'batch_size', 'type': int, 'default': 1000,
               'help': 'Retrieve this amount of records from solr in one time, defaults to 1000'},
              ]

    def run(self):
        from pyoko.conf import settings
        from importlib import import_module
        import_module(settings.MODELS_MODULE)
        registry = import_module('pyoko.model').model_registry
        model_name = self.manager.args.model
        if model_name != 'all':
            models = [registry.get_model(name) for name in model_name.split(',')]
        else:
            models = registry.get_base_models()
        batch_size = self.manager.args.batch_size
        tree = self.manager.args.tree
        pretty = self.manager.args.pretty

        data = defaultdict(list)
        for mdl in models:
            model = mdl(super_context)
            count = model.objects.count()
            rounds = count / batch_size + 1
            bucket = model.objects.bucket
            for i in range(rounds):
                for obj in model.objects.data().raw('*:*',
                                                    sort="timestamp asc",
                                                    rows=batch_size,
                                                    start=i * batch_size):
                    if obj.data is not None:
                        if not tree:
                            print(json.dumps((bucket.name, obj.key, obj.data)))
                        else:
                            data[bucket.name].append((obj.key, obj.data))
        if tree:
            if pretty:
                out = json.dumps(data, sort_keys=True, indent=4)
            else:
                out = json.dumps(data)
            print(out)


class LoadData(Command):
    CMD_NAME = 'load_data'
    HELP = 'Reads JSON data from given file and populates models'
    PARAMS = [{'name': 'file', 'required': True,
               'help': 'Path of the data file'},
              {'name': 'tree', 'action': 'store_true',
               'help': 'Set this to load a JSON file previously dumped with "--tree" flag.'},
              {'name': 'overwrite', 'action': 'store_true',
               'help': 'Overwrites existing records. First gets then updates.'},

              # {'name': 'pretty', 'action': 'store_true', 'help': 'Pretty print'},
              # {'name': 'batch_size', 'type': int, 'default': 1000,
              #  'help': 'Batch size, defaults to 1000'},
              ]

    def run(self):
        from pyoko.conf import settings
        from importlib import import_module
        import_module(settings.MODELS_MODULE)
        registry = import_module('pyoko.model').model_registry
        self.buckets = {}
        self.record_counter = 0
        for mdl in registry.get_base_models():
            bucket = mdl(super_context).objects.bucket
            self.buckets[bucket.name] = bucket
        with codecs.open(self.manager.args.file, encoding='utf-8') as file:
            if self.manager.args.tree:
                self.read_whole_file(file)
            else:
                self.read_per_line(file)
        if self.record_counter:
            print("%s record(s) inserted." % self.record_counter)

    def read_whole_file(self, file):
        data = json.loads(file.read())
        for bucket_name in data.keys():
            for key, val in data[bucket_name]:
                self.save_obj(bucket_name, key, val)

    def read_per_line(self, file):
        for line in file:
            bucket_name, key, val = json.loads(line)
            self.save_obj(bucket_name, key, val)

    def save_obj(self, bucket_name, key, val):
        if self.manager.args.overwrite:
            obj = self.buckets[bucket_name].get(key)
            obj.data = val
            obj.store()
        else:
            self.buckets[bucket_name].new(key, val).store()
        self.record_counter += 1


class FindEmptyRecords(Command):
    CMD_NAME = '_find_empty'
    HELP = 'tests the correctness of the output of the bucket.get_keys()'

    def run(self):
        from pyoko.conf import settings
        from importlib import import_module
        import_module(settings.MODELS_MODULE)
        registry = import_module('pyoko.model').model_registry
        models = registry.get_base_models()
        empty_records = set()
        seen_in = defaultdict(list)
        for mdl in models:
            bucket = mdl.objects.bucket
            for k in bucket.get_keys():
                obj = bucket.get(k)
                if obj.data is None:
                    empty_records.add(k)
                    seen_in[k].append(bucket.name)
        for mdl in models:
            bucket = mdl.objects.bucket
            for k in list(empty_records):
                obj = bucket.get(k)
                if obj.data is not None:
                    empty_records.remove(k)
                    print("%s seen in %s" % (obj.key, seen_in[obj.key]))
                    print("But actually found in %s" % (obj.key, bucket))
                    print("\n------\n")

        if empty_records:
            print("These keys cannot found anywhere: %s" % empty_records)
