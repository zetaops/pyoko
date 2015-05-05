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
from pyoko.db.solriakcess import SolRiakcess



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
        model_names = []
        for key in attrs:
            if hasattr(attrs[key], '__base__') and \
                            attrs[key].__base__.__name__ in ('ListModel', 'Model'):
            # if attrs[key].__class__ == mcs:
                model_names.append(key)
        new_class = super(ModelMeta, mcs).__new__(mcs, name, bases, attrs)
        new_class.model_names = model_names
        _registry.register_model(new_class)
        return new_class


class Model(object):
    __metaclass__ = ModelMeta
    DataSource = Enum('DataSource', 'None Solr Riak')

    def __init__(self, **kwargs):
        self.key = None
        self.path = []
        self.obj_cache = {}
        self._loaded_from = self.DataSource.None
        self.objects = SolRiakcess()
        self.instantiate_submodels()
        self._init_properties(kwargs)
        self._set_node_paths()
        # self._mark_linked_models()

    def instantiate_submodels(self):
        for key in self.model_names:
            self.obj_cache[key] = getattr(self, key)()
            self.obj_cache[key].instantiate_submodels()

    def __call__(self, *args, **kwargs):
        self._init_properties(kwargs)
        return self

    def load_class(self, name):
        pass

    def clean(self):
        pass

    # def _mark_linked_models(self):
    #     for k, v in self.__class__.__dict__.items():
    #         ins = getattr(self, k)
    #         if isinstance(ins, (Model, ListModel)):

    def _init_properties(self, kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k) and isinstance(getattr(self, k), field.BaseField):
                self.__setattr__(k, v)

    def _set_node_paths(self):
        for k, v in self.__class__.__dict__.items():
            ins = getattr(self, k)
            if isinstance(ins, (Model, ListModel)):
                ins.path = self.path + [self.__class__.__name__.lower()]
                ins._set_node_paths()


    def __setattr__(self, name, value):
        attr = getattr(self, name, None)
        if isinstance(attr, field.BaseField):
            # attr.set_value(value)
            self.obj_cache[name] = copy.deepcopy(attr)
            self.obj_cache[name].set_value(value)
        else:
            super(Model, self).__setattr__(name, value)

    def __getattribute__(self, key):
        if key in super(Model, self).__getattribute__('obj_cache'):
        # try:
            return super(Model, self).__getattribute__('obj_cache')[key]
        else:
        # except KeyError:
            return super(Model, self).__getattribute__(key)

    def collect_index_fields(self):
        result = []
        multi = isinstance(self.__class__, ListModel)
        for k in self.__class__.__dict__:
            ins = getattr(self, k)
            if isinstance(ins, field.BaseField) and ins.index:
                result.append((k, ins.__class__.__name__.lower(), multi))
            elif isinstance(ins, Model):
                result.extend(ins.collect_index_fields())
        return result

    def clean_value(self):
        dct = {}
        for k, v in self.obj_cache.items():
            dct[k] = v.clean_value()
        return dct

    def save(self):

        data_dict = self.clean_value()
        pprint(data_dict)
            # dict((k, getattr(self, k)) for k in self.__class__.__dict__
        #                  if not self._meta[k].link_type
        #                  and hasattr(self, k))
        # for field in data_dict:
        #     if self._meta[field].link_type and self._meta[field].backref:
        #         value = getattr(self, field)
        # self.db.save()



class ListModel(Model):

    def __init__(self, **kwargs):
        super(ListModel, self).__init__(**kwargs)
        self.values = []

    def __call__(self, **kwargs):
        clone = self.__class__(**kwargs)
        # clone.instantiate_submodels()
        # clone._init_properties(kwargs)
        self.values.append(clone)
        return clone

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
            dct = {}
            print ins
            if hasattr(ins, 'obj_cache'):
                for k, v in ins.obj_cache.items():
                    dct[k] = v.clean_value()
            elif hasattr(ins, 'clean_value'):
                dct[ins.__name__] = ins.clean_value()
            else:
                dct[self.__class__.__name__] = ins
            lst.append(dct)
        return lst

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
