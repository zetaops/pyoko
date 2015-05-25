# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

from enum import Enum
from pyoko import field
from pyoko.exceptions import NotCompatible
from pyoko.db.base import DBObjects

# TODONE: refactor model and data fields in a manner that not need __getattribute__, __setattr__
# TODONE: complete save method
# TODONE: update solr schema creation routine for new "store" option
# TODONE: add tests for class schema to json conversion
# TODONE: add tests for solr schema creation
# NOT-TODONE: prepare temporary riak env [ "test server" support removed from riak 2.0 ]
# TODONE: IMPORTANT::: schema updates should not cause API changes!!!
# TODO: add tests for save, filter
# TODO: implement Model population from db results
# TODO: implement ListModel population from db results
# TODO: implement versioned data update mechanism (based on Redis?)
# TODO: Add AbstractBase Model Support
# TODO: implement one-to-many
# TODO: implement many-to-many
# TODO: Add validation checks
# TODO: Check for missing magic methods and add if needed.
# TODO: Add Migration support with automatic 'schema_version' field.
# TODO: Add backwards migrations

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
        base_fields = {}
        if bases[0].__name__ == 'Base':
            attrs.update(bases[0]._DEFAULT_BASE_FIELDS)
        for key in list(attrs.keys()):
            if hasattr(attrs[key], '__base__') and attrs[key].__base__.__name__ in ('ListModel', 'Model'):
                models[key] = attrs.pop(key)
            elif hasattr(attrs[key], 'clean_value'):
                attrs[key].name = key
                base_fields[key] = attrs[key]

        new_class = super(ModelMeta, mcs).__new__(mcs, name, bases, attrs)
        new_class._models = models
        new_class._fields = base_fields
        _registry.register_model(new_class)
        return new_class


DataSource = Enum('DataSource', 'None Cache Solr Riak')


class Base(object):
    _DEFAULT_BASE_FIELDS = {
        'archived': field.Boolean(default=False, index=True, store=True),
        'timestamp': field.Date(index=True, store=True),
        '_deleted': field.Boolean(default=False, index=True, store=False)}

    def __init__(self, **kwargs):
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
    """
    Sub-models are moved to _models[] attribute in ModelMeta,
    then replaced to instance model at _instantiate_submodels()

    Since fields are defined as descriptors, they can access to instance they called from but
    we can't access their methods and attributes from model instance.
    I've solved this issue by copying fields in to _fields[] attribute of model instance in ModelMeta
    so we access field values from _field_values[] attribute, fields themselves from _fields[]

    """
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
        self._field_values = {}
        self._context = self.__defaults.copy()
        self._context.update(kwargs.pop('_context', {}))
        self._parse_meta_attributes()
        self._instantiate_submodels()
        self._set_fields_values(kwargs)


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

    def __call__(self, *args, **kwargs):
        self._set_fields_values(kwargs)
        return self

    def _set_fields_values(self, kwargs):
        for k in self._fields:
            self._field_values[k] = kwargs.get(k)

    def _collect_index_fields(self):
        result = []
        multi = isinstance(self, ListModel)
        for name, field_ins in self._fields.items():
            if field_ins.index or field_ins.store:
                result.append((self._path_of(name),
                               field_ins.__class__.__name__,
                               field_ins.index_as,
                               field_ins.index,
                               field_ins.store,
                               multi))
        for mdl_ins in self._models:
            result.extend(getattr(self, mdl_ins)._collect_index_fields())
        return result

    def _load_data(self, name):
        pass

    # ######## Public Methods  #########

    def clean_value(self):
        dct = {}
        for name in self._models:
            dct[name] = getattr(self, name).clean_value()
        for name, field_ins in self._fields.items():
            dct[name] = field_ins.clean_value(self._field_values[name])
        return dct


class ListModel(Model):
    def __init__(self, **kwargs):
        super(ListModel, self).__init__(**kwargs)
        self.values = []
        self.models = []

    # ######## Public Methods  #########

    def clean_value(self):
        """
        :return: [{},]
        """
        return [super(ListModel, mdl).clean_value() for mdl in self.models]


    # ######## Python Magic  #########

    def __call__(self, **kwargs):
        clone = self.__class__(**kwargs)
        self.models.append(clone)
        return clone

    def __len__(self):
        return len(self.models)
    #
    # def __getitem__(self, key):
    #     # if key is of invalid type or value, the list values will raise the error
    #     return self.values[key]
    #
    # def __setitem__(self, key, value):
    #     self.values[key] = value
    #
    # def __delitem__(self, key):
    #     del self.values[key]

    def __iter__(self):
        return iter(self.models)
