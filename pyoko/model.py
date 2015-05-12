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
from pyoko.exceptions import NotCompatible
from pyoko.lib.utils import DotDict
from pyoko.db.base import DBObjects

# TODONE: refactor model and data fields in a manner that not need __getattribute__, __setattr__
# TODONE: complete save method
# TODONE: update solr schema creation routine for new "store" option
# TODONE: add tests for class schema to json conversion
# TODO: add tests for solr schema creation
# TODO: check for missing tests
# TODO: add missing tests
# TODO: implement Model population from db results
# TODO: implement ListModel population from db results
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
        clean_fields = {}
        field_names = []
        for key in list(attrs.keys()):
            if hasattr(attrs[key], '__base__') and attrs[key].__base__.__name__ in ('ListModel', 'Model'):
                models[key] = attrs.pop(key)
            elif hasattr(attrs[key], 'clean_value'):
                attrs[key].name = key
                field_names.append(key)
                clean_fields[key] = attrs[key].clean_value

        new_class = super(ModelMeta, mcs).__new__(mcs, name, bases, attrs)
        new_class._models = models
        new_class._clean_fields = clean_fields
        new_class._field_names = field_names
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

    __defaults = {
        'cache': None,
        'index': None,
        'store': None,
        'required': True,
    }

    def __init__(self, **kwargs):
        super(Model, self).__init__()
        self.key = None
        self.path = []
        self._fields = {}
        self._context = self.__defaults.copy()
        self._context.update(kwargs.pop('_context', {}))
        self._parse_meta_attributes()
        self._embed_fields()
        self._instantiate_submodels()
        self._set_fields_values(kwargs)
        # self._set_node_paths()
        # self._mark_linked_models()

    def _parse_meta_attributes(self):
        if hasattr(self, 'Meta'):
            self._context.update({k: v for k, v in self.Meta.__dict__.items()
                                  if not k.startswith('__')})

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
            ins.path = self.path + [self.__class__.__name__.lower()]
            setattr(self, name, ins)
            # self.obj_cache[key] = getattr(self, key)(_context=self._context)
            # self.obj_cache[key].path = self.path + [self.__class__.__name__.lower()]
            # self.obj_cache[key]._instantiate_submodels()

    def _embed_fields(self):
        """
        reinstantiates data fields of model as instance properties.
        """
        for name, klass in self._fields.items():
            setattr(self, name, copy.deepcopy(klass))

    def __call__(self, *args, **kwargs):
        self._set_fields_values(kwargs)
        return self

    def _load_data(self, name):
        pass

    def _set_fields_values(self, kwargs):
        for k in self._field_names:
            self._fields[k] = kwargs.get(k)

    def _collect_index_fields(self):
        result = []
        multi = isinstance(self, ListModel)
        for field_name, field_ins in self.__dict__.items():
            if isinstance(field_ins, field.BaseField) and (
                        field_ins.index or field_ins.store):
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
        for name in self._models:
            dct[name] = getattr(self, name).clean_value()
        for name, func in self._clean_fields.items():
            dct[name] = func(self._fields[name])
        return dct


class ListModel(Model):
    def __init__(self, **kwargs):
        super(ListModel, self).__init__(**kwargs)
        self.values = []
        self.models = []

    # ######## Public Methods  #########

    def add(self, **datadict):
        # Currently this method only usable on ListModels that doesnt contain another model.
        # if user update a ListModel in this way, than codes that use this method has to be updated too!
        # TODO: IMPORTANT::: schema updates should not cause a API changes!!!
        assert not self._models, NotCompatible
        self.values.append(DotDict(datadict or self._fields))

    def clean_value(self):
        """
        currently a ListModel can contain values(list of dicts) or objects(list of it's instances)
        but not both.
        :return: dict
        """
        lst = []
        if self.values:
            for val in self.values:
                dct = {}
                for field_name, clean_func in self._clean_fields.items():
                    dct[field_name] = clean_func(val[field_name])
                lst.append(dct)
        elif self.models:
            for ins in self.models:
                dct = {}
                for name, clean_func in ins._clean_fields.items():
                    dct[name] = clean_func(ins._fields[name])
                for mdl_name in ins._models:
                    dct[mdl_name] = getattr(ins, mdl_name).clean_value()
                lst.append(dct)
        return lst

    # ######## Python Magic  #########

    def __call__(self, **kwargs):
        clone = self.__class__(**kwargs)
        self.models.append(clone)
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
