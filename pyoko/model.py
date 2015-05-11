# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import copy
from pprint import pprint
from enum import Enum

from pyoko import field
from pyoko.db.connection import http_client
from pyoko.lib.utils import DotDict
from pyoko.db.base import DBObjects

# TODONE: refactor model and data fields in a manner that not need __getattribute__, __setattr__
# TODONE: complete save method
# TODO: update solr schema creation routine for new "store" option
# TODO: add tests for class schema to json conversion
# TODO: add tests for class schema / json conversion
# TODO: add tests for solr schema creation
# TODO: check for missing tests
# TODO: add missing tests
# TODO: implement model population from db results
# TODO: add tests
# TODO: implement versioned data update mechanism (based on Redis?)
# TODO: add tests
# TODO: implement one-to-many (also based on Redis?)
# TODO: add tests

class Registry(object):
    def __init__(self):
        self.registry = []

    def register_model(self, cls):
        if cls.__name__ == 'Model':
            return
        self.registry += [cls]

        # def class_by_bucket_name(self, bucket_name):
        #     for model in self.registry:
        #         if model.bucket_name == bucket_name:
        #             return model


_registry = Registry()


class ModelMeta(type):
    def __new__(mcs, name, bases, attrs):
        models = {}
        fields = {}
        for key in list(attrs.keys()):
            if hasattr(attrs[key], '__base__') and attrs[key].__base__.__name__ in ('ListModel', 'Model'):
                models[key] = attrs.pop(key)
            elif hasattr(attrs[key], 'clean_value'):
                fields[key] = attrs.pop(key)

        new_class = super(ModelMeta, mcs).__new__(mcs, name, bases, attrs)
        new_class._models = models
        new_class._fields = fields
        _registry.register_model(new_class)
        return new_class


DataSource = Enum('DataSource', 'None Cache Solr Riak')

class Base(object):

    def __init__(self, **kwargs):
        self._deleted = field.Boolean(default=False, index=True, store=False)
        self._archived = field.Boolean(default=False, index=True, store=True)
        self._timestamp = field.Timestamp()
        self._riak_object = None
        self._loaded_from = DataSource.None
        self.objects = DBObjects(model=self)
        super(Base, self).__init__(**kwargs)


    def save(self):
        data_dict = self.clean_value()
        self.objects.save()

    def delete(self):
        self._deleted = True
        self.save()

class Model(object):
    __metaclass__ = ModelMeta

    # # Standard fields
    # _deleted = field.Boolean(default=False, index=True, store=False)
    # _archived = field.Boolean(default=False, index=True, store=True)
    # _timestamp = field.Timestamp()


    def __init__(self, **kwargs):
        super(Model, self).__init__()
        self.__models = {}
        self.__fields = {}
        self.key = None
        self.path = []
        self.obj_cache = {}
        self._is_child = False
        self._context = kwargs.pop('_context', {})
        self._parse_meta_attributes()
        self._embed_fields()
        self._instantiate_submodels()
        self._set_fields(kwargs)
        # self._set_node_paths()
        # self._mark_linked_models()

    def _parse_meta_attributes(self):
        return {k: v for k, v in self.Meta.__dict__.items() if not k.startswith('__')} if hasattr(self, 'Meta') else {}

    def _get_bucket_name(self):
        self._context.get('bucket_name', self.__class__.__name__.lower())

    def _path_of(self, prop):
        """
        returns the dotted path of the given model attribute
        """
        return '.'.join(list(self.path + [self.__class__.__name__.lower(), prop])[1:])

    # _GLOBAL_CONF = []
    def _instantiate_submodels(self):
        """
        instantiate all submodels, pass path data and flag them as child
        """
            # child nodes should inherit GLOBAL_CONFigurations
            # conf = {(k, v) for k, v in self._context.items() if k in self._GLOBAL_CONF}
        for name, klass in self._models.items():
            ins = klass(_context=self._context)
            ins.path= self.path + [self.__class__.__name__.lower()]
            ins._is_child = True
            setattr(self, name, ins)
            # self.obj_cache[key] = getattr(self, key)(_context=self._context)
            # self.obj_cache[key].path = self.path + [self.__class__.__name__.lower()]
            # self.obj_cache[key]._is_child = True
            # self.obj_cache[key]._instantiate_submodels()

    def _embed_fields(self):
        """
        reinstantiates data fields of model as instance properties.
        """
        for name, klass in self._fields.items():
            setattr(self, name, copy.deepcopy(klass))

    def __call__(self, *args, **kwargs):
        self._set_fields(kwargs)
        return self

    def _load_data(self, name):
        pass

    def _set_fields(self, kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def _collect_index_fields(self):
        result = []
        multi = isinstance(self, ListModel)
        for field_name, field_ins in self.__dict__.items():
            if isinstance(field_ins, field.BaseField) and (field_ins.index or field_ins.store):
                result.append((self._path_of(field_name),
                               field_ins.__class__.__name__,
                               field_ins.index_as,
                               field_ins.index,
                               field_ins.store,
                               multi))
            elif isinstance(field_ins, Model):
                result.extend(field_ins._collect_index_fields())
        return result

    # ######## Public Methods  #########

    def clean_value(self):
        dct = {}
        for k, v in self.__fields.items() + self.__models.items():
            dct[k] = v.clean_value()
        return dct





class ListModel(Model):
    def __init__(self, **kwargs):
        super(ListModel, self).__init__(**kwargs)
        self.values = []

    # ######## Public Methods  #########

    def add(self, **datadict):
        # extract data fields from subclasses and store them appropriately
        #
        # for k, v in datadict.items():
        #     if isinstance(getattr(self, k), (ListModel, Model)):
        #         datadict.pop(k)
        self.values.append(DotDict(datadict))

    def clean_value(self):
        lst = []
        for ins in self.values:
            if hasattr(ins, 'obj_cache'):
                dct = {}
                for k, v in ins.obj_cache.items():
                    dct[k] = v.clean_value()
                lst.append(dct)
            elif hasattr(ins, 'clean_value'):
                # TODO: check if this case necessary / exists
                lst.append({ins.__name__: ins.clean_value()})
            else:
                lst.append(ins)
        return lst

    # ######## Python Magic  #########

    def __call__(self, **kwargs):
        clone = self.__class__(**kwargs)
        # clone.instantiate_submodels()
        # clone._init_properties(kwargs)
        self.values.append(clone)
        return clone

    def __len__(self):
        return len(self.values)

    def __getitem__(self, key):
        # if key is of invalid type or value, the list values will raise the error
        return self.values[key]

    def __setitem__(self, key, value):
        self.values[key] = value

    def __delitem__(self, key):
        del self.values[key]

    def __iter__(self):
        return iter(self.values)
