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
import re
import json

import time
from os import environ
import os
import sys
from riak import ConflictError

from pyoko.conf import settings
from riak.client import binary_json_decoder, binary_json_encoder
from sys import argv, stdout
from six import add_metaclass, PY2
from pyoko.model import super_context
from pyoko.lib import utils
from pyoko.exceptions import ObjectDoesNotExist


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
    Holds the given command line  parameters in self.manager.args

    Attributes:
        CMD_NAME: name of your command
        HELP: help texts starts with "R|" will be parsed as raw text
        PARAMS: A dictionary list with following possible values.

            - name: name of parameter
            - help: help text for parameter. Parsed as raw if starts with "R|"
            - required: Optional. Set True if this  is a required parameter.
            - default: Optional. Define a default value for the parameter
            - action: 'store_true' see the official argparse documentation for more info
    """

    # https://docs.python.org/2/howto/argparse.html
    # https://docs.python.org/2/library/argparse.html

    def _make_manager(self, kw):
        """
        Creates a fake ``manage`` object to implement clean
        API for the management commands.

        Args:
            kw: keyword args to be construct fake manage.args object.

        Returns:
            Fake manage object.
        """
        for param in self.PARAMS:
            if param['name'] not in kw:
                store_true = 'action' in param and param['action'] == 'store_true'
                kw[param['name']] = param.get('default', False if store_true else None)
        return type('FakeCommandManager', (object,),
                    {
                        'args': type('args', (object,), kw)
                    })

    def __init__(self, manager=None, **kwargs):
        self.manager = manager or self._make_manager(kwargs)

    def run(self):
        """
        This is where the things are done.
        You should override this method in your command class.
        """
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
            exec ('from %s import *' % settings.MODELS_MODULE)
        try:
            from IPython import start_ipython
            start_ipython(argv=[], user_ns=locals())
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
    HELP = 'REALLY DELETES the contents of models'
    PARAMS = [{'name': 'model', 'required': True,
               'help': 'Models name(s) to be cleared. Say "all" to clear all models'},
              {'name': 'exclude',
               'help': 'Models name(s) to be excluded, comma separated'},
              {'name': 'wait_sync', 'action': 'store_true',
               'help': 'Wait till indexes synced. Default: False'
                       'Wait till flushing reflects to indexes.'},
              ]

    def run(self):
        from pyoko.conf import settings
        from pyoko.model import super_context
        from importlib import import_module
        import_module(settings.MODELS_MODULE)
        registry = import_module('pyoko.model').model_registry
        model_name = self.manager.args.model
        if model_name != 'all':
            models = [registry.get_model(name) for name in model_name.split(',')]
        else:
            models = registry.get_base_models()
            if self.manager.args.exclude:
                excluded_models = [registry.get_model(name) for name in
                                   self.manager.args.exclude.split(',')]
                models = [model for model in models if model not in excluded_models]

        for mdl in models:
            num_of_records = mdl(super_context).objects._clear()
            print("%s object(s) deleted from %s " % (num_of_records, mdl.__name__))
        if self.manager.args.wait_sync:
            for mdl in models:
                while mdl(super_context).objects.count():
                    time.sleep(0.3)


class ReIndex(Command):
    CMD_NAME = 'reindex'
    HELP = 'Re-indexes model objects'
    PARAMS = [{'name': 'model', 'required': True,
               'help': 'Models name(s) to be cleared. Say "all" to clear all models'},
              {'name': 'exclude',
               'help': 'Models name(s) to be excluded, comma separated'},
              {'name': 'include_deleted', 'action': 'store_true',
               'help': 'Reindex object even if it was deleted'}
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
            if self.manager.args.exclude:
                excluded_models = [registry.get_model(name) for name in
                                   self.manager.args.exclude.split(',')]
                models = [model for model in models if model not in excluded_models]

        for mdl in models:
            stream = mdl.objects.adapter.bucket.stream_keys()
            i = 0
            unsaved_keys = []
            for key_list in stream:
                for key in key_list:
                    #i += 1
                    # time.sleep(0.4)
                    try:
                        mdl.objects.get(key).save()
                        i += 1
                        # obj = mdl.bucket.get(key)
                        # if obj.data:
                        #     obj.store()
                    except ObjectDoesNotExist:
                        if self.manager.args.include_deleted:
                            o = mdl.objects.filter(key=key, deleted=True)[0]
                            o.save()
                            i += 1
                            print("Deleted object found: %s " % o.key)

                    except ConflictError:
                        unsaved_keys.append(key)
                        print("Error on save. Record in conflict: %s > %s" % (mdl.__name__, key))
                    except:
                        unsaved_keys.append(key)
                        print("Error on save! %s > %s" % (mdl.__name__, key))
                        import traceback

                        traceback.print_exc()
            stream.close()
            print("Re-indexed %s records of %s" % (i, mdl.__name__))
            if unsaved_keys:
                print("\nThese keys cannot be updated:\n\n", unsaved_keys)


class SmartFormatter(HelpFormatter):
    def _split_lines(self, text, width):
        # this is the RawTextHelpFormatter._split_lines
        if text.startswith('R|'):
            return text[2:].splitlines()
        return HelpFormatter._split_lines(self, text, width)


class ManagementCommands(object):
    """
    All management commands executed by this class.
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
        if self.args.daemonize:
            self.daemonize()
        else:
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
            sub_parser.add_argument("--daemonize", action="store_true", help="Run in background")
            if hasattr(cmd, 'PARAMS'):
                for params in cmd.PARAMS:
                    param = params.copy()
                    name = "--%s" % param.pop("name")
                    # params['des']
                    if 'action' not in param:
                        param['nargs'] = '?'
                    sub_parser.add_argument(name, **param)

        self.args = parser.parse_args(args)

    def daemonize(self):
        import sys
        try:
            pid = os.fork()
            if pid > 0:
                # Exit first parent

                sys.exit(0)
        except OSError as e:
            print(sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror))
            sys.exit(1)

        # Decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # Do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # Exit from second parent; print eventual PID before exiting
                print("Daemon PID %d" % pid)
                sys.exit(0)
        except OSError as e:
            print(sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror))
            sys.exit(1)
        self.args.command()


class BaseDumpHandler(object):
    """The base class for different implementations of data dump handlers."""
    EXTENSION = 'dump'

    def __init__(self, models, batch_size, per_model=False, output_path='', remove_dumped=False):
        self._models = models
        self._batch_size = batch_size
        self._per_model = per_model
        self._output_path = output_path
        self._remove_dumped = remove_dumped

    def _prepare_output_multi(self, model):
        """If printing to a different file per model, change the file for the current model"""
        model_name = model.__name__
        current_path = os.path.join(self._output_path, '{model}.{extension}'.format(
            model=model_name,
            extension=self.EXTENSION,
        ))
        self._outfile = codecs.open(current_path, 'w', encoding='utf-8')
        print('Dumping {model} to {file}'.format(model=model_name, file=current_path))

    def dump_data(self):
        if self.single_file:
            self._outfile = codecs.open(self._output_path, 'w', encoding='utf-8')
            print('Dumping to file {path}'.format(path=self._output_path))

        for mdl in self._models:

            if self.multi_file:
                self._prepare_output_multi(mdl)
            elif self.single_file:
                print('Dumping {model}'.format(model=mdl.__name__))

            model = mdl(super_context)
            count = model.objects.count()
            rounds = int(count / self._batch_size) + 1
            bucket = model.objects.adapter.bucket

            self.pre_dump_hook(bucket)
            for i in range(rounds):

                start = 0 if self._remove_dumped else i

                data = model.objects.data().raw('*:*').set_params(
                    sort="timestamp asc",
                    rows=self._batch_size,
                    start=start * self._batch_size,
                )

                try:
                    for value, key in data:
                        if value is not None:
                            self.handle_data(bucket, key, value)
                            self.post_handle_data_hook(bucket, key, value)
                    if self._remove_dumped:
                        # wait 1 second to pass for next round
                        print("removed dumped objects from riak, waiting for solr sync")
                        time.sleep(5)
                except ValueError:
                    raise
            self.post_dump_hook(bucket)

    def write(self, data):
        if self._output_path:
            self._outfile.write(data + '\n')
        else:
            print(data)

    def handle_data(self, bucket, key, value):
        raise RuntimeError('Subclasses must override handle_data method!')

    def pre_handle_data_hook(self, bucket, key, value):
        pass

    def post_handle_data_hook(self, bucket, key, value):
        if self._remove_dumped:
            bucket.delete(key)

    def pre_dump_hook(self, bucket):
        pass

    def post_dump_hook(self, bucket):
        pass

    @property
    def single_file(self):
        return self._output_path and not self._per_model

    @property
    def multi_file(self):
        return self._output_path and self._per_model


class JSONDumpHandler(BaseDumpHandler):
    """Writes each line as a separate JSON document.
    Unlike "json_tree", memory usage does not increase with the number of records."""
    EXTENSION = 'json'

    def handle_data(self, bucket, key, value):
        self.write(json.dumps((bucket.name, key, value)))


class TreeDumpHandler(BaseDumpHandler):
    """DO NOT use on big DBs. Writes whole dump as a big JSON object."""
    EXTENSION = 'json'

    def __init__(self, *args, **kwargs):
        super(TreeDumpHandler, self).__init__(*args, **kwargs)
        self._collected_data = defaultdict(list)

    def handle_data(self, bucket, key, value):
        self._collected_data[bucket.name].append((key, value))

    def post_dump_hook(self, bucket):
        self.write(json.dumps(self._collected_data))


class PrettyDumpHandler(TreeDumpHandler):
    """DO NOT use on big DBs. Formatted version of json_tree."""
    def post_dump_hook(self, bucket):
        self.write(json.dumps(self._collected_data, sort_keys=True, indent=4))


class CSVDumpHandler(BaseDumpHandler):
    """This is the default format. Writes one record per line.
    Since it bypasses the JSON encoding/decoding,
    it's much faster and memory efficient than others."""
    EXTENSION = 'csv'

    def handle_data(self, bucket, key, value):
        self.write('{bucket}/|{key}/|{value}'.format(
            bucket=bucket.name,
            key=key,
            value=value if PY2 else value.decode('utf-8'),
        ))

    def pre_dump_hook(self, bucket):
        bucket.set_decoder('application/json', lambda a: a)

    def post_dump_hook(self, bucket):
        bucket.set_decoder('application/json', binary_json_decoder)


class DumpData(Command):
    # FIXME: Should be refactored to a backend agnostic form
    CMD_NAME = 'dump_data'
    HELP = 'Dumps all data to stdout or to given file'
    DUMP_HANDLERS = {
        'csv': CSVDumpHandler,
        'json': JSONDumpHandler,
        'json_tree': TreeDumpHandler,
        'pretty': PrettyDumpHandler,
    }
    PARAMS = [
        {'name': 'model', 'required': True,
         'help': 'Models name(s) to be dumped. Say "all" to dump all models'},
        {'name': 'path', 'required': False,
         'help': 'Instead of stdout, write to given file'},

        {'name': 'type', 'default': 'csv', 'choices': DUMP_HANDLERS.keys(),
         'help': """R|
                csv: {csv}

                json: {json}

                json_tree: {json_tree}

                pretty: {pretty}

                """.format(**{name: handler.__doc__ for name, handler in DUMP_HANDLERS.items()})
         },
        {'name': 'batch_size', 'type': int, 'default': 1000,
         'help': 'Retrieve this amount of records from Solr in one time, defaults to 1000'},
        {'name': 'per_model', 'action': 'store_true', 'default': False,
         'help': 'Split the dumps per model, placing the data of each model into a seperate file. '
                 'When this setting is used, path is required and should refer to a directory, '
                 'in which the dumps will be placed.'},
        {'name': 'exclude',
         'help': 'Models name(s) to be excluded, comma separated'},
        {'name': 'remove_dumped', 'action': 'store_true', 'default': False,
         'help': 'Remove dumped data from database'}
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
            try:
                models = [registry.get_model(name) for name in model_name.split(',')]
            except KeyError as err:
                print('Model {model} does not exist!'.format(model=err.args[0]))
                sys.exit(1)
        else:
            models = registry.get_base_models()
            if self.manager.args.exclude:
                excluded_models = [registry.get_model(name) for name in
                                   self.manager.args.exclude.split(',')]
                models = [model for model in models if model not in excluded_models]

        batch_size = self.manager.args.batch_size
        type_ = self.manager.args.type
        output_path = self.manager.args.path
        per_model = self.manager.args.per_model
        remove_dumped = self.manager.args.remove_dumped

        # If per model dumps are requested, the path must be specified and must be a directory
        if per_model and not output_path:
            print('If per model dumps are requested, the path must be given!')
            sys.exit(1)
        if per_model and not os.path.isdir(output_path):
            print('If per model dumps are requested, the path must be a directory!')
            sys.exit(1)

        dump_handler = self.DUMP_HANDLERS[type_](models, batch_size, per_model,
                                                 output_path, remove_dumped)
        dump_handler.dump_data()


class LoadData(Command):
    # FIXME: Should be refactored to a backend agnostic form
    """
    Loads previously dumped data into DB.
    """
    CMD_NAME = 'load_data'
    HELP = 'Reads JSON data from given file and populates models'

    CSV = 'csv'
    JSON = 'json'
    TREE = 'json_tree'
    PRETTY = 'pretty'
    CHOICES = (CSV, JSON, TREE, PRETTY)
    PARAMS = [
        {'name': 'path', 'required': True, 'help': """R|Path of the data file or fixture directory.
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
                self.record_counter = 0
                self.already_existing = 0
        else:
            self.read_file(self.manager.args.path)
        for mdl in self.registry.get_base_models():
            if self.typ == self.CSV:
                mdl(super_context).objects.adapter.bucket.set_encoder("application/json",
                                                                      binary_json_encoder)

    def prepare_buckets(self):
        """
        loads buckets to bucket cache. disables the default json encoders if CSV is selected
        """
        for mdl in self.registry.get_base_models():
            bucket = mdl(super_context).objects.adapter.bucket
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




    def read_whole_file(self, file):
        data = json.loads(file.read())
        for bucket_name in data.keys():
            for key, val in data[bucket_name]:
                self.save_obj(bucket_name, key, val)

    def read_per_line(self, file):
        for line in file:
            bucket_name, key, val = line.split('/|')
            self.save_obj(bucket_name, key, val.strip())

    def read_json_per_line(self, file):
        for line in file:
            bucket_name, key, val = json.loads(line)
            self.save_obj(bucket_name, key, val)

    def save_obj(self, bucket_name, key, val):
        key = key or None
        if key is None:
            data = val.encode('utf-8') if self.typ == self.CSV else val
            self.buckets[bucket_name].new(key, data).store()
            self.record_counter += 1
        else:
            obj = self.buckets[bucket_name].get(key)
            if not obj.exists or self.manager.args.update:
                obj.data = val.encode('utf-8') if self.typ == self.CSV else val
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
            bucket = mdl.objects.adapter.bucket
            for k in bucket.get_keys():
                obj = bucket.get(k)
                if obj.data is None:
                    empty_records.add(k)
                    seen_in[k].append(bucket.name)
        if empty_records:
            print("Found %s empty records" % len(empty_records))
            for mdl in models:
                print("Searching wrong keys in %s" % (mdl.Meta.verbose_name,))
                bucket = mdl.objects.adapter.bucket
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


class GenerateDiagrams(Command):
    CMD_NAME = 'generate_diagrams'
    HELP = 'Generate PlantUML diagrams from the models.'
    SPLIT_APP = 'app'
    SPLIT_MODEL = 'model'
    SPLIT_NO = 'no'
    SPLIT_CHOICES = (SPLIT_NO, SPLIT_APP, SPLIT_MODEL)
    PARAMS = [
        {'name': 'model', 'required': False, 'default': 'all',
         'help': 'Models name(s) to generate diagrams for. Say "all" to generate diagrams for all models'},
        {'name': 'path', 'required': False,
         'help': 'Instead of stdout, write to given file'},
        {'name': 'split', 'default': SPLIT_NO, 'choices': SPLIT_CHOICES,
         'help': """R|
               %s : Generates a single diagram containing all models.

               %s: Generates seperate diagrams for each app. Requires path.

               %s: Generates seperate diagrams for each model. Requires path.
               """ % SPLIT_CHOICES
         }
    ]

    # Representations of the different link types
    _one_to_one = '"1" -- "1"'
    _one_to_many = '"1" -- "0..*"'
    _many_to_many = '"0..*" -- "0..*"'
    # Markers used to denote required and null
    _marker_true = '*'
    _marker_false = ' '
    # Extra padding, placed after field names and types
    _padding_after_name = 3
    _padding_after_type = 2
    # Class start and end delimiters
    _class_start = '\n\nclass %s<<(M,orchid)>>{'
    _class_end = '}\n'
    # Markers for the start and end of the apps
    _app_start = '\npackage %s{'
    _app_end = '}'
    # The beginning and the end of the diagram
    _diagram_start = """@startuml

skinparam classAttributeFontName Monospaced
skinparam classBackgroundColor #FFFFFF
skinparam classBorderColor #D8D8D8
skinparam packageBorderColor #BDBDBD
skinparam classArrowColor #0B615E
skinparam shadowing false

title
<size:24>Entity Based Model Diagram</size>
( All Models extends <b>pyoko.Model</b> class )
endtitle
"""
    _diagram_end = "@enduml"
    # Prefixes for the items
    _field_prefix = '  '
    _nodelist_field_prefix = '|_'
    # The function used to print output. Replaced with one that prints to file when path is given
    _print = print

    def run(self):
        from pyoko.conf import settings
        from importlib import import_module
        import_module(settings.MODELS_MODULE)
        registry = import_module('pyoko.model').model_registry
        selected_models = self.manager.args.model
        apps_models = registry.get_models_by_apps()
        selected_by_app = list()
        # Pick the selected models from each app
        for app, app_models in apps_models:
            if selected_models != 'all':
                selected_from_app = [model for model in app_models
                                     if model().title in selected_models.split(',')]
            else:
                selected_from_app = app_models
            if len(selected_from_app) > 0:
                selected_by_app.append((app, selected_from_app))
        to_file = self.manager.args.path
        split_type = self.manager.args.split
        if to_file and split_type == self.SPLIT_APP:
            self._print_split_app(to_file, selected_by_app)
        if to_file and split_type == self.SPLIT_MODEL:
            self._print_split_model(to_file, selected_by_app)
        else:
            self._print_single_file(to_file, selected_by_app)

    def _print_split_model(self, path, apps_models):
        """
        Print each model in apps_models into its own file.
        """
        for app, models in apps_models:
            for model in models:
                model_name = model().title
                if self._has_extension(path):
                    model_path = re.sub(r'^(.*)[.](\w+)$', r'\1.%s.%s.\2' % (app, model_name), path)
                else:
                    model_path = '%s.%s.%s.puml' % (path, app, model_name)
                self._print_single_file(model_path, [(app, [model])])

    def _print_split_app(self, path, apps_models):
        """
        Print each app in apps_models associative list into its own file.
        """
        for app, models in apps_models:
            # Convert dir/file.puml to dir/file.app.puml to print to an app specific file
            if self._has_extension(path):
                app_path = re.sub(r'^(.*)[.](\w+)$', r'\1.%s.\2' % app, path)
            else:
                app_path = '%s.%s.puml' % (path, app)

            self._print_single_file(app_path, [(app, models)])

    def _print_single_file(self, path, apps_models):
        """
        Print apps_models which contains a list of 2-tuples containing apps and their models
        into a single file.
        """
        if path:
            outfile = codecs.open(path, 'w', encoding='utf-8')
            self._print = lambda s: outfile.write(s + '\n')
        self._print(self._diagram_start)
        for app, app_models in apps_models:
            self._print_app(app, app_models)
        self._print(self._diagram_end)
        if path:
            outfile.close()

    def _print_app(self, app, models):
        """
        Print the models of app, showing them in a package.
        """
        self._print(self._app_start % app)
        self._print_models(models)
        self._print(self._app_end)

    def _print_models(self, models):
        # Generate the models & their fields
        for mdl in models:
            model = mdl(super_context)
            self._print(self._class_start % model.title)
            fields = []
            fields.extend(self._get_model_fields(model))
            links = model.get_links(link_source=True)
            fields.extend(self._format_links_fields(links))
            fields.append(('', '', '', ''))  # Empty line
            fields.extend(self._format_listnodes(self._get_model_nodes(model)))
            self._print_fields(fields)
            self._print(self._class_end)
            # Generate the links of the current model
            self._print_links(model, links)

    def _print_fields(self, fields):
        """Print the fields, padding the names as necessary to align them."""
        # Prepare a formatting string that aligns the names and types based on the longest ones
        longest_name = max(fields, key=lambda f: len(f[1]))[1]
        longest_type = max(fields, key=lambda f: len(f[2]))[2]
        field_format = '%s%-{}s %-{}s %s'.format(
            len(longest_name) + self._padding_after_name,
            len(longest_type) + self._padding_after_type)
        for field in fields:
            self._print(field_format % field)

    def _format_listnodes(self, listnodes):
        """
        Format ListNodes and their fields into tuples that can be printed with _print_fields().
        """
        fields = list()
        for name, node in listnodes:
            fields.append(('--', '', '', '--'))
            fields.append(('', '**%s(ListNode)**' % name, '', ''))
            for link in node.get_links():
                linked_model = link['mdl'](super_context)
                null = self._marker_true if link['null'] is True else self._marker_false
                fields.append((self._nodelist_field_prefix, link['field'],
                               '%s()' % linked_model.title, null))
            fields.extend(self._get_model_fields(node, self._nodelist_field_prefix))
        return fields

    def _get_model_fields(self, model, prefix=_field_prefix):
        """
        Find all fields of given model that are not default models.
        """
        fields = list()
        for field_name, field in model()._ordered_fields:
            # Filter the default fields
            if field_name not in getattr(model, '_DEFAULT_BASE_FIELDS', []):
                type_name = utils.to_camel(field.solr_type)
                required = self._marker_true if field.required is True else self._marker_false
                fields.append((prefix, field_name, type_name, required))

        return fields

    def _get_model_nodes(self, model):
        """
        Find all the non-auto created nodes of the model.
        """
        nodes = [(name, node) for name, node in model._nodes.items()
                if node._is_auto_created is False]
        nodes.sort(key=lambda n: n[0])
        return nodes

    def _format_links_fields(self, links):
        """
        Format the fields containing links into 4-tuples printable by _print_fields().
        """
        fields = list()
        for link in links:
            linked_model = link['mdl'](super_context)
            null = self._marker_true if link['null'] is True else self._marker_false
            # In LinkProxy, if reverse_name is empty then only reverse has the name
            # of the field on the link_source side
            field_name = link['field'] or link['reverse']
            fields.append((self._field_prefix, field_name, '%s()' % linked_model.title, null))
        fields.sort(key=lambda f: f[1])
        return fields

    def _print_links(self, model, links):
        """
        Print links that start from model.
        """
        for link in links:
            if link['o2o'] is True:
                link_type = self._one_to_one
            elif link['m2m'] is True:
                link_type = self._many_to_many
            else:
                link_type = self._one_to_many
            linked_model = link['mdl'](super_context)
            self._print('%s %s %s' % (model.title, link_type, linked_model.title))

    @staticmethod
    def _has_extension(path):
        """
        Returns true if path ends with an extension.
        """
        return re.search(r'^.*[.]\w+$', path) is not None