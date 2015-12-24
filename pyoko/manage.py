#!/usr/bin/env python
# -*-  coding: utf-8 -*-
"""
command line management interface
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from __future__ import print_function
from argparse import RawTextHelpFormatter, HelpFormatter
import codecs
from collections import defaultdict
import json

from os import environ
import os

from pyoko.conf import settings
from riak.client import binary_json_decoder, binary_json_encoder
from sys import argv, stdout
from six import add_metaclass, PY2
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
    """
    Command object is a thin wrapper around Python's powerful argparse module.

    ::Class Properties::

    *CMD_NAME*: name of your command
    *HELP*: help texts starts with "R|" will be parsed as raw text
    *PARAMS*: = [{
        'name': name of parameter
        'help': help text for parameter. Parsed as raw if starts with "R|"
        'required': Optional. Set True if this  is a required parameter.
        'default': Optional. Define a default value for the parameter
        'action': 'store_true' see the official argparse
            *documentation for more info
    }]
    * https://docs.python.org/2/howto/argparse.html
    * https://docs.python.org/2/library/argparse.html

    """

    def __init__(self, manager):
        """
        :param manager: holds the given cli parameters in self.manager.args
        :return:
        """
        self.manager = manager

    def run(self):
        raise NotImplemented("You should override this method in your command class")


class Shell(Command):
    CMD_NAME = 'shell'
    PARAMS = [
              {'name': 'no_model', 'action': 'store_true',
               'help': 'Do not import models'},
              ]
    HELP = 'Run IPython shell'

    def run(self):
        if not self.manager.args.no_model:
            exec('from %s import *' % settings.MODELS_MODULE)
        try:
            from IPython import embed
            embed()
        except:
            import readline
            import code
            vars = globals().copy()
            vars.update(locals())
            shell = code.InteractiveConsole(vars)
            shell.interact()


class SchemaUpdate(Command):
    CMD_NAME = 'migrate'
    PARAMS = [{'name': 'model', 'required': True, 'help': 'Models name(s) to be updated.'
                                                          ' Say "all" to update all models'},
              {'name': 'threads', 'default': 1, 'help': 'Max number of threads. Defaults to 1'},
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
            print("%s object(s) deleted from %s " % (num_of_records, mdl.__name__))


class SmartFormatter(HelpFormatter):
    def _split_lines(self, text, width):
        # this is the RawTextHelpFormatter._split_lines
        if text.startswith('R|'):
            return text[2:].splitlines()
        return HelpFormatter._split_lines(self, text, width)


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
        if self.args.timeit:
            import time
            t1 = time.time()
        self.args.command()
        if self.args.timeit:
            print("Process took %s seconds" % round(time.time() - t1, 2))

    def parse_args(self, args):
        import argparse
        parser = argparse.ArgumentParser(formatter_class=SmartFormatter)
        subparsers = parser.add_subparsers(title='Possible commands')
        for cmd_class in self.commands:
            cmd = cmd_class(self)
            sub_parser = subparsers.add_parser(cmd.CMD_NAME, help=getattr(cmd, 'HELP', None),
                                               formatter_class=SmartFormatter)
            sub_parser.set_defaults(command=cmd.run)
            sub_parser.add_argument("--timeit", action="store_true", help="Time the process")
            if hasattr(cmd, 'PARAMS'):
                for params in cmd.PARAMS:
                    param = params.copy()
                    name = "--%s" % param.pop("name")
                    # params['des']
                    if 'action' not in param:
                        param['nargs'] = '?'
                    sub_parser.add_argument(name, **param)

        self.args = parser.parse_args(args)


class DumpData(Command):
    CMD_NAME = 'dump_data'
    HELP = 'Dumps all data to stdout or to given file'
    CSV = 'csv'
    JSON = 'json'
    TREE = 'json_tree'
    PRETTY = 'pretty'
    CHOICES = (CSV, JSON, TREE, PRETTY)
    PARAMS = [
        {'name': 'model', 'required': True,
         'help': 'Models name(s) to be dumped. Say "all" to dump all models'},
        {'name': 'path', 'required': False,
         'help': 'Instead of stdout, write to given file'},

        {'name': 'type', 'default': CSV, 'choices': CHOICES,
         'help': """R|
                %s : This is the default format. Writes one record per line.
                     Since it bypasses the JSON encoding/decoding,
                     it's much faster and memory efficient than others.

                %s: Writes each line as a separate JSON document. Unlike "json_tree", memory usage
                    does not increase with the number of records.

                %s: DO NOT use on big DBs. Writes whole dump as a big JSON object.

                %s: DO NOT use on big DBs. Formatted version of json_tree.

                """ % CHOICES
         },
        {'name': 'batch_size', 'type': int, 'default': 1000,
         'help': 'Retrieve this amount of records from Solr in one time, defaults to 1000'},
    ]

    def run(self):
        from pyoko.conf import settings
        from importlib import import_module
        import os
        try:
            import_module(settings.MODELS_MODULE)
        except:
            # weird but this is enough to prevent a strange riak error
            # http://pastebin.com/HiPRmAhM
            raise
        registry = import_module('pyoko.model').model_registry
        model_name = self.manager.args.model
        if model_name != 'all':
            models = [registry.get_model(name) for name in model_name.split(',')]
        else:
            models = registry.get_base_models()
        batch_size = self.manager.args.batch_size
        typ = self.manager.args.type
        to_file = self.manager.args.path
        if to_file:
            outfile = codecs.open(self.manager.args.path, 'w', encoding='utf-8')
        data = defaultdict(list)
        for mdl in models:
            if to_file:
                print("Dumping %s" % mdl.__name__)
            model = mdl(super_context)
            count = model.objects.count()
            rounds = int(count / batch_size) + 1
            bucket = model.objects.bucket
            if typ == self.CSV:
                bucket.set_decoder('application/json', lambda a: a)
            for i in range(rounds):
                for obj in model.objects.data().raw('*:*',
                                                    sort="timestamp asc",
                                                    rows=batch_size,
                                                    start=i * batch_size):
                    # print("Object %s" % obj.key)
                    if obj.data is not None:
                        if typ == self.JSON:
                            out = json.dumps((bucket.name, obj.key, obj.data))
                            if to_file:
                                outfile.write(out + "\n")
                            else:
                                print(out)
                        elif typ == self.TREE:
                            data[bucket.name].append((obj.key, obj.data))
                        elif typ == self.CSV:
                            if PY2:
                                out = bucket.name + "/|" + obj.key + "/|" + obj.data
                                if to_file:
                                    outfile.write(out + "\n")
                                else:
                                    print(out)
                            else:
                                out = bucket.name + "/|" + obj.key + "/|" + obj.data.decode('utf-8')
                                if to_file:
                                    outfile.write(out + "\n")
                                else:
                                    print(out)
            bucket.set_decoder('application/json', binary_json_decoder)
        if typ in [self.TREE, self.PRETTY]:
            if typ == self.PRETTY:
                out = json.dumps(data, sort_keys=True, indent=4)
            else:
                out = json.dumps(data)
            if to_file:
                outfile.write(out)
            else:
                print(out)
        if to_file:
            outfile.close()


class LoadData(Command):
    CMD_NAME = 'load_data'
    HELP = 'Reads JSON data from given file and populates models'

    CSV = 'csv'
    JSON = 'json'
    TREE = 'json_tree'
    PRETTY = 'pretty'
    CHOICES = (CSV, JSON, TREE, PRETTY)
    PARAMS = [
        {'name': 'path', 'required': True, 'help':"""R|Path of the data file or fixture directory.
When loading from a directory, files with .csv (for CSV format)
and .js extensions will be loaded."""},
        {'name': 'update', 'action': 'store_true',
         'help': 'Overwrites existing records. '
                 'Since this will not check for the existence of an object, it runs a bit faster.'},
        {'name': 'type', 'default': CSV, 'choices': CHOICES,
         'help': 'Defaults to "csv". See help of dump_data command for more details'
         },
        {'name': 'batch_size', 'type': int, 'default': 1000,
         'help': 'Retrieve this amount of objects from Solr in one time, defaults to 1000'},
    ]

    def run(self):
        from pyoko.conf import settings
        from importlib import import_module
        import_module(settings.MODELS_MODULE)
        self.registry = import_module('pyoko.model').model_registry
        self.typ = self.manager.args.type
        self.buckets = {}
        self.record_counter = 0
        self.already_existing = 0
        self.prepare_buckets()

        if os.path.isdir(self.manager.args.path):
            from glob import glob
            ext = 'csv' if self.typ is self.CSV else 'js'
            for file in glob(os.path.join(self.manager.args.path, "*.%s" % ext)):
                self.read_file(file)
        else:
            self.read_file(self.manager.args.path)

    def prepare_buckets(self):
        """
        loads buckets to bucket cache. disables the default json encoders if CSV is selected
        :return:
        """
        for mdl in self.registry.get_base_models():
            bucket = mdl(super_context).objects.bucket
            if self.typ == self.CSV:
                bucket.set_encoder("application/json", lambda a: a)
            self.buckets[bucket.name] = bucket

    def read_file(self, file_path):
        with codecs.open(file_path, encoding='utf-8') as file:
            if self.typ in (self.TREE, self.PRETTY):
                self.read_whole_file(file)
            elif self.typ == self.JSON:
                self.read_json_per_line(file)
            else:
                self.read_per_line(file)

        if self.record_counter:
            print("%s object(s) inserted." % self.record_counter)

        if self.already_existing:
            print("%s existing object(s) NOT updated." % self.already_existing)

        for mdl in self.registry.get_base_models():
            if self.typ == self.CSV:
                mdl(super_context).objects.bucket.set_encoder("application/json",
                                                              binary_json_encoder)

    def read_whole_file(self, file):
        data = json.loads(file.read())
        for bucket_name in data.keys():
            for key, val in data[bucket_name]:
                self.save_obj(bucket_name, key, json.dumps(val))

    def read_per_line(self, file):
        for line in file:
            bucket_name, key, val = line.split('/|')
            self.save_obj(bucket_name, key, val.strip())

    def read_json_per_line(self, file):
        for line in file:
            bucket_name, key, val = json.loads(line)
            self.save_obj(bucket_name, key, json.dumps(val))

    def save_obj(self, bucket_name, key, val):
        key = key or None
        if self.manager.args.update or key is None:
            self.buckets[bucket_name].new(key, val.encode('utf-8')).store()
            self.record_counter += 1
        else:
            obj = self.buckets[bucket_name].get(key)
            if not obj.exists:
                obj.data = val.encode('utf-8')
                obj.store()
                self.record_counter += 1
            else:
                self.already_existing += 1


class TestGetKeys(Command):
    CMD_NAME = '_test_get_keys'
    HELP = 'tests the correctness of the bucket.get_keys()'

    def run(self):
        from pyoko.conf import settings
        from importlib import import_module
        import_module(settings.MODELS_MODULE)
        registry = import_module('pyoko.model').model_registry
        models = registry.get_base_models()
        empty_records = set()
        seen_in = defaultdict(list)
        for mdl in models:
            print("Checking keys of %s" % mdl.Meta.verbose_name)
            bucket = mdl.objects.bucket
            for k in bucket.get_keys():
                obj = bucket.get(k)
                if obj.data is None:
                    empty_records.add(k)
                    seen_in[k].append(bucket.name)
        if empty_records:
            print("Found %s empty records" % len(empty_records))
            for mdl in models:
                print("Searching wrong keys in %s" % (mdl.Meta.verbose_name,))
                bucket = mdl.objects.bucket
                for k in list(empty_records):
                    obj = bucket.get(k)
                    if obj.data is not None:
                        empty_records.remove(k)
                        print("%s seen in %s" % (obj.key, seen_in[obj.key]))
                        print("But actually found in %s" % bucket.name)
                        print("- - -")

            print("These keys cannot found anywhere: %s" % empty_records)
        else:
            print("\n\nEverything looks OK!")


class FindDuplicateKeys(Command):
    CMD_NAME = '_find_dups'
    HELP = 'finds duplicate keys, to help debugging'

    def run(self):
        from pyoko.conf import settings
        from importlib import import_module
        import_module(settings.MODELS_MODULE)
        registry = import_module('pyoko.model').model_registry
        models = registry.get_base_models()
        keys = defaultdict(list)
        for mdl in models:
            print("Checking keys of %s" % mdl.Meta.verbose_name)
            model = mdl(super_context)
            is_mdl_ok = True
            for r in model.objects.solr().raw('*:*'):
                if r['_yz_rk'] in keys:
                    print("%s found in %s previously seen in %s" % (r['_yz_rk'],
                                                                    mdl.__name__,
                                                                    keys[r['_yz_rk']]))
                    is_mdl_ok = False
                keys[r['_yz_rk']].append(mdl.__name__)
            if is_mdl_ok:
                print("~~~~~~~~ %s is OK!" % mdl.Meta.verbose_name)

