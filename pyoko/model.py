# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from collections import defaultdict
from copy import deepcopy
import time

from enum import Enum
from six import add_metaclass
from pyoko import field
from pyoko.db.base import DBObjects

# TODO: implement versioned data update mechanism
# TODO: implement one-to-many
# TODO: implement many-to-many
# TODO: Add validation checks
# TODO: Check for missing magic methods and add if needed.
# TODO: Add Migration support with automatic 'schema_version' field.
# TODO: Add backwards migrations

# region ModelMeta and Registry
from pyoko.lib.utils import un_camel


class Registry(object):
    def __init__(self):
        self.registry = []
        self.link_registry = defaultdict(list)

    def register_model(self, cls):
        if cls._TYPE == 'Model' and cls not in self.registry:
            self.registry += [cls]
            for name, link_model in cls._linked_models.items():
                self.link_registry[link_model].append(cls)
                setattr(link_model, '%ss' % cls.__name__, cls)

    def get_base_models(self):
        return self.registry

        # def class_by_bucket_name(self, bucket_name):
        #     for model in self.registry:
        #         if model.bucket_name == bucket_name:
        #             return model



_registry = Registry()


class ModelMeta(type):
    def __new__(mcs, name, bases, attrs):

        nodes = {}
        linked_models = {}
        base_fields = {}
        # print(getattr(bases[0], '_TYPE', bases[0]))
        class_type = getattr(bases[0], '_TYPE', None)

        if class_type == 'Model':
            attrs.update(bases[0]._DEFAULT_BASE_FIELDS)

        for key in list(attrs.keys()):
            if hasattr(attrs[key], '__base__'):
                attr_type = getattr(attrs[key].__base__, '_TYPE', '')
                if attr_type == 'Node':
                    nodes[key] = attrs.pop(key)
            else:
                attr_type = getattr(attrs[key], '_TYPE', '')
                if attr_type == 'Model':
                    linked_model_base_instance = attrs[key]
                    attrs[key] = deepcopy(linked_model_base_instance)
                    linked_models[key] = linked_model_base_instance.__class__
                elif attr_type == 'Field':
                    attrs[key].name = key
                    base_fields[key] = attrs[key]
        attrs['_nodes'] = nodes
        attrs['_fields'] = base_fields
        attrs['_linked_models'] = linked_models
        new_class = super(ModelMeta, mcs).__new__(mcs, name, bases, attrs)
        if new_class._TYPE == 'Model':
            new_class.objects = DBObjects(model_class=new_class)
        _registry.register_model(new_class)
        return new_class
# endregion





@add_metaclass(ModelMeta)
class Node(object):
    """
    We move sub-models in to _nodes[] attribute at ModelMeta,
    then replace to instance model at _instantiate_nodes()

    Since fields are defined as descriptors,
    they can access to instance they called from but
    we can't access their methods and attributes from model instance.
    I've kinda solved it by copying fields in to _fields[] attribute of
    model instance at ModelMeta.

    So, we access field values from _field_values[] attribute
    and fields themselves from _fields[]

    """
    _TYPE = 'Node'
    objects = DBObjects
    __defaults = {
        'cache': None,
        'index': None,
        'store': None,
        'required': True,
    }

    def __init__(self, **kwargs):
        super(Node, self).__init__()
        self.key = None
        self.path = []
        self._parent = None
        self._field_values = {}
        self._context = self.__defaults.copy()
        self._context.update(kwargs.pop('_context', {}))
        self.objects = self._context.get('objects', self.objects)
        self._instantiate_nodes()
        self._set_fields_values(kwargs)
        self.objects.model = self
        self.objects.model_class = self.__class__



    @classmethod
    def _get_bucket_name(cls):
        return getattr(cls.Meta, 'bucket_name', cls.__name__.lower())

    def _path_of(self, prop):
        """
        returns the dotted path of the given model attribute
        """
        return '.'.join(list(self.path + [un_camel(self.__class__.__name__),
                                          prop]))

    def _instantiate_nodes(self):
        """
        instantiate all nodes, pass path data
        """
        for name, klass in self._nodes.items():
            ins = klass(_context=self._context)
            ins.path = self.path + [self.__class__.__name__.lower()]
            setattr(self, name, ins)

    def __call__(self, *args, **kwargs):
        self._set_fields_values(kwargs)
        return self

    def _set_fields_values(self, kwargs):
        for name in self._fields:
            setattr(self, name, kwargs.get(name))
            # self._field_values[k] = kwargs.get(k)
        for name in self._linked_models:
            assignment = kwargs.get(name)
            if assignment:
                setattr(self, name, assignment)
            # self._field_values[k] = kwargs.get(k)

    def _collect_index_fields(self, base_name=None, in_multi=False):
        if not base_name:
            base_name = self._get_bucket_name()
        result = []
        multi = in_multi or isinstance(self, ListNode)
        for name, field_ins in self._fields.items():
            field_name = self._path_of(name).replace(base_name + '.', '')
            result.append((field_name,
                           field_ins.solr_type,
                           field_ins.index,
                           field_ins.store,
                           multi))
        for mdl_ins in self._nodes:
            result.extend(getattr(self, mdl_ins)._collect_index_fields(base_name, multi))
        return result

    def _load_data(self, data):
        for name in self._nodes:
            _name = un_camel(name)
            if _name in data:
                getattr(self, name)._load_data(data[_name])
        self._set_fields_values(data)
        return self
        # for name, field_ins in self._fields.items():
        #     self._field_values[name] = data[name]

    # ######## Public Methods  #########

    def clean_value(self):
        dct = {}
        for name in self._nodes:
            dct[un_camel(name)] = getattr(self, name).clean_value()
        if self._linked_models:
            dct['_cache'] = {}
            for name in self._linked_models:
                obj = getattr(self, name)
                if obj.key:
                    dct['_cache'][un_camel(name)] = obj.clean_value()
                    dct['_cache'][un_camel(name)]['key'] = obj.key
        for name, field_ins in self._fields.items():
            # if field_ins
            dct[un_camel(name)] = field_ins.clean_value(self._field_values[name])
        return dct

class Model(Node):
    _TYPE = 'Model'
    _DEFAULT_BASE_FIELDS = {
        'archived': field.Boolean(default=False, index=True, store=True),
        'timestamp': field.TimeStamp(),
        'deleted': field.Boolean(default=False, index=True, store=False)}

    class Meta(object):
        bucket_type = 'models'

    def __init__(self, context=None, **kwargs):
        self._riak_object = None
        self._context = context or {}
        self.row_level_access()
        self._prepare_linked_models()

        # self.filter_cells()
        super(Model, self).__init__(**kwargs)
        # print("\n init \n ")
        # print(id(self.__class__))

    def _load_data(self, data):
        super(Model, self)._load_data(data)
        cache = data.get('_cache', {})
        for name in self._linked_models:
            _name = un_camel(name)
            if _name in cache:
                getattr(self, name)._load_data(cache[_name])
        return self

    def _prepare_linked_models(self):
        """
        prepare linked models
        """
        for name, model in self._linked_models.items():
            model._parent = self

    def _load_from_parent(self):
        pass

    def row_level_access(self):
        """
        Define your query filters in here to enforce row level access control
        self._context should contain required user attributes and permissions
        eg:
            self.objects = self.objects.filter(user_in=self._context.user['id'])
        """
        pass

    def save(self):
        self.objects.save_model()

    def delete(self):
        self.deleted = True
        self.save()



class ListNode(Node):
    def __init__(self, **kwargs):
        super(ListNode, self).__init__(**kwargs)
        self.values = []
        self.node_stack = []

    # ######## Public Methods  #########

    def _load_data(self, data):
        """

        """
        for node_data in data:
            clone = self.__class__(**node_data)
            for name in self._nodes:
                _name = un_camel(name)
                if _name in node_data: # check for partial data
                    getattr(clone, name)._load_data(node_data[_name])
            self.node_stack.append(clone)

    def clean_value(self):
        """
        :return: [{},]
        """
        return [super(ListNode, mdl).clean_value() for mdl in self.node_stack]

    # ######## Python Magic  #########

    def __call__(self, **kwargs):
        clone = self.__class__(**kwargs)
        self.node_stack.append(clone)
        return clone

    def __len__(self):
        return len(self.node_stack)

    #
    # def __getitem__(self, key):
    #     # if key is of invalid type or value,
    # the list values will raise the error
    #     return self.values[key]
    #
    # def __setitem__(self, key, value):
    #     self.values[key] = value
    #
    # def __delitem__(self, key):
    #     del self.values[key]

    def __iter__(self):
        return iter(self.node_stack)
