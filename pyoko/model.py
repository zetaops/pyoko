# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from collections import defaultdict
from six import add_metaclass
import six
from pyoko import field
from pyoko.conf import settings
from pyoko.db.base import DBObjects
from pyoko.lib.utils import un_camel, un_camel_id


# TODO: implement versioned data update mechanism
# TODO: implement one-to-many
# TODO: implement many-to-many
# TODO: Add validation checks
# TODO: Check for missing magic methods and add if needed.
# TODO: Add Migration support with automatic 'schema_version' field.
# TODO: Add backwards migrations

# region ModelMeta and Registry
class Registry(object):
    def __init__(self):
        self.registry = []
        self.link_registry = defaultdict(list)
        self.back_link_registry = defaultdict(list)

    def register_model(self, kls):
        if kls not in self.registry:
            # register model to base registry
            self.registry += [kls]
            for name, link_model in kls._linked_models.items():
                # register models that linked from this model
                self.link_registry[link_model].append((name, kls))
                # register models that gives (back)links to this model
                self.back_link_registry[kls].append((name, un_camel(kls.__name__), link_model))
                print(kls, self.back_link_registry[kls])
                instance = getattr(kls, name)
                if instance._is_one_to_one:
                    kl = kls(one_to_one=True)
                    kl._is_auto_created_reverse_link = True
                    setattr(link_model, un_camel(kls.__name__), kl)
                    link_model._linked_models[un_camel(kls.__name__)] = kls
                else:
                    # other side of n-to-many should be a ListNode named with a "_set" suffix and
                    # our linked_model as the sole element of the listnode
                    reverse_model_set_name = '%s_set' % un_camel(kls.__name__)
                    kl = kls()
                    kl._is_auto_created_reverse_link = True
                    listnode = type(reverse_model_set_name, (ListNode,),
                                    {un_camel(kls.__name__): kl})
                    listnode._linked_models[un_camel(kls.__name__)] = kls
                    link_model._nodes[reverse_model_set_name] = listnode

    def get_base_models(self):
        return self.registry


_registry = Registry()


# noinspection PyMissingConstructor
class ModelMeta(type):
    def __init__(mcs, name, bases, attrs):
        if mcs.__base__.__name__ == 'Model':
            # add models to _registry
            mcs.objects = DBObjects(model_class=mcs)
            _registry.register_model(mcs)

            # setup relations for linked models which lives in a ListNode (1-n n-n)
            # for node_name in attrs['_nodes']:
            #     mcs._many_to_models.update(node._linked_models)

            #### for model_name, model in node._linked_models.items():

    def __new__(mcs, name, bases, attrs):
        base_model_class = bases[0]
        class_type = getattr(base_model_class, '_TYPE', None)
        if class_type == 'Model':
            mcs.process_models(attrs, base_model_class)
        mcs.process_attributes(attrs)
        new_class = super(ModelMeta, mcs).__new__(mcs, name, bases, attrs)
        return new_class

    @staticmethod
    def process_attributes(attrs):
        """
        we're iterating over attributes of the soon to be created class object.
        :param dict attrs: attribute dict
        """
        attrs['_nodes'] = {}
        attrs['_linked_models'] = {}
        attrs['_fields'] = {}
        attrs['_many_to_models'] = {}

        for key, attr in list(attrs.items()):
            # if it's a class (not instance) and it's type is Node
            if hasattr(attr, '__base__') and getattr(attr.__base__, '_TYPE', '') == 'Node':
                attrs['_nodes'][key] = attrs.pop(key)
            else:  # otherwise it should be a field or linked model instance
                attr_type = getattr(attr, '_TYPE', '')
                if attr_type == 'Model':
                    attrs['_linked_models'][key] = attr.__class__
                elif attr_type == 'Field':
                    attr.name = key
                    attrs['_fields'][key] = attr

    @staticmethod
    def process_models(attrs, base_model_class):
        """
        Attach default fields and meta options to models
        :param dict attrs: attribute dict
        :param bases:
        """
        attrs.update(base_model_class._DEFAULT_BASE_FIELDS)
        meta = attrs.get('META', {})
        copy_of_base_meta = base_model_class._META.copy()
        copy_of_base_meta.update(meta)
        attrs['META'] = copy_of_base_meta


# endregion





@add_metaclass(ModelMeta)
class Node(object):
    """
    We store node classes in _nodes[] attribute at ModelMeta,
    then replace them with their instances at _instantiate_nodes()

    Likewise we store linked models in _linked_models[]

    Since fields are defined as descriptors,
    they can access to instance they called from but
    we can't access to their methods and attributes from model instance.
    I've kinda solved it by copying fields in to _fields[] attribute of
    model instance at ModelMeta. So, we get values of fields from _field_values[]
    and access to fields themselves from _fields[]

    """
    _TYPE = 'Node'

    def __init__(self, **kwargs):
        super(Node, self).__init__()
        self.key = None
        self.path = []
        self._parent = None
        self._field_values = {}
        self._instantiate_nodes()
        self._set_fields_values(kwargs)

    @classmethod
    def _get_bucket_name(cls):
        return cls._META.get('bucket_name', cls.__name__.lower())

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
            ins = klass()
            ins.path = self.path + [self.__class__.__name__.lower()]
            setattr(self, name, ins)

    def __repr__(self):
        try:
            u = six.text_type(self)
        except (UnicodeEncodeError, UnicodeDecodeError):
            u = '[Bad Unicode data]'
        return six.text_type('<%s: %s>' % (self.__class__.__name__, u))

    def __str__(self):
        if six.PY2 and hasattr(self, '__unicode__'):
            return six.text_type(self).encode('utf-8')
        return '%s object' % self.__class__.__name__

    def __call__(self, *args, **kwargs):
        self._set_fields_values(kwargs)
        return self

    def _set_fields_values(self, kwargs):
        for name in self._fields:
            if name in kwargs:
                setattr(self, name, kwargs.get(name, self._field_values.get(name)))
        for name in self._linked_models:
            linked_model = kwargs.get(name)
            if linked_model:
                setattr(self, name, linked_model)


    def _collect_index_fields(self, model_name=None, in_multi=False):
        """
        collects fields which will be indexed
        :param str model_name: base Model's name
        :param bool in_multi: if we are in a ListNode or not
        :return: [(field_name, solr_type, is_indexed, is_stored, is_multi]
        """
        result = []
        if not model_name:

            model_name = self._get_bucket_name()
            for name in self._linked_models:
                obj = getattr(self, name)
                result.append((un_camel_id(name), 'string', True, True, obj.has_many_values()))
        multi = in_multi or isinstance(self, ListNode)
        for name, field_ins in self._fields.items():
            field_name = self._path_of(name).replace(model_name + '.', '')
            result.append((field_name,
                           field_ins.solr_type,
                           field_ins.index,
                           field_ins.store,
                           multi))
        for mdl_ins in self._nodes:
            result.extend(getattr(self, mdl_ins)._collect_index_fields(model_name, multi))
        return result

    def _load_data(self, data):
        """
        fills model instance (and sub-nodes and linked model instances)
         with the data returned from riak
        :param dict data:
        :return: self
        """
        self._data = data
        for name in self._nodes:
            _name = un_camel(name)
            if _name in data:
                new = getattr(self, name).__class__()
                new._load_data(data[_name])
                setattr(self, name, new)
        self._set_fields_values(data)
        return self
        # for name, field_ins in self._fields.items():
        #     self._field_values[name] = data[name]

    # ######## Public Methods  #########

    def clean_value(self):
        """
        generates a json serializable representation of the model data
        :rtype: dict
        :return: riak ready python dict
        """
        dct = {}
        for name in self._nodes:
            dct[un_camel(name)] = getattr(self, name).clean_value()
        if self._linked_models:
            dct['_cache'] = {}
            for name in self._linked_models:
                obj = getattr(self, name)
                dct[un_camel_id(name)] = obj.key or ''
                if not obj._is_auto_created_reverse_link and obj.key:
                    dct['_cache'][un_camel(name)] = obj.clean_value()
                    dct['_cache'][un_camel(name)]['key'] = obj.key
        for name, field_ins in self._fields.items():
            # if name in self._field_values:
            dct[un_camel(name)] = field_ins.clean_value(self._field_values.get(name))
        return dct


class Model(Node):
    objects = DBObjects
    _TYPE = 'Model'
    _META = {
        'bucket_type': settings.DEFAULT_BUCKET_TYPE
    }
    _is_auto_created_reverse_link = False
    _DEFAULT_BASE_FIELDS = {
        'timestamp': field.TimeStamp(),
        'deleted': field.Boolean(default=False, index=True)}

    def __init__(self, context=None, **kwargs):
        self._riak_object = None
        self.key = None
        self.context = context or {}
        self.row_level_access()
        self._prepare_linked_models()
        self._is_one_to_one = kwargs.pop('one_to_one', False)
        self.title = kwargs.pop('title', self.__class__.__name__)
        # self.filter_cells()



        super(Model, self).__init__(**kwargs)
        self.objects.model = self
        self.objects.model_class = self.__class__

    def set_data(self, data):
        """
        first calls supers load_data
        then fills linked models
        :param data:
        :return:
        """
        self._load_data(data)
        cache = data.get('_cache', {})
        if cache:
            for name in self._linked_models:
                _name = un_camel(name)
                if _name in cache:
                    mdl = getattr(self, name)
                    mdl.key = cache[_name]['key']
                    mdl.set_data(cache[_name])
        return self

    def has_many_values(self):
        """
        is this model represents multiple instances of itself eg: ManyToMany, ManyToOne
        :return:
        """
        return False

    def _prepare_linked_models(self):
        """
        prepare linked models
        """
        for name, model in self._linked_models.items():
            model._parent = self

    def _load_from_parent(self):
        """
        this method will be invoked by a field instance of an empty linked model

        :return:
        """
        pass

    def row_level_access(self):
        """
        Define your query filters in here to enforce row level access control
        self._config should contain required user attributes and permissions
        eg:
            self.objects = self.objects.filter(user_in=self._config.user['id'])
        """
        pass

    def _get_reverse_links(self):
        """
        get reverse linked models from model registry
        :return: [Model]
        """
        return _registry.link_registry[self.__class__]

    def _get_forward_links(self):
        """
        get reverse linked models from model registry
        :return: [Model]
        """
        return _registry.back_link_registry[self.__class__]

    def save(self, dont_save_backlinks=False):
        self.objects.save_model()
        if not dont_save_backlinks:  # to avoid a reciprocal save loop
            self._save_backlinked_models()
        return self

    def _save_backlinked_models(self):
        # TODO: when called from a deleted object, instead of updating we should remove it from target
        for name, mdl in self._get_reverse_links():
            for obj in mdl.objects.filter(**{un_camel_id(name): self.key}):
                setattr(obj, name, self)
                # obj.save()
                obj.save(dont_save_backlinks=mdl._is_auto_created_reverse_link)
        for pointer, name, mdl in self._get_forward_links():
            obj = mdl.objects.get(getattr(self, pointer).key)
            back_linking_model = getattr(obj, name, None)
            if back_linking_model:
                is_auto_created = getattr(obj, name, None)._is_auto_created_reverse_link
                setattr(obj, name, self)
                obj.save(dont_save_backlinks=is_auto_created)
            else:
                object_set = getattr(obj, '%s_set' % name)
                object_set.add(**{name:self})
                obj.save(dont_save_backlinks=True)


    def delete(self):
        self.deleted = True
        self.save()


class ListNode(Node):
    """
    Currently we disregard the ordering when updating items of a ListNode
    """
    def __init__(self, **kwargs):
        super(ListNode, self).__init__(**kwargs)
        self.values = []
        self.node_stack = []
        self._data = []
        self._is_item = False

    # ######## Public Methods  #########

    def _load_data(self, data):
        """
        just stores the data at self._data, actual object creation done at _generate_instances()
        """
        self._data = data

    def _generate_instances(self, data):
        """
        a clone generator that will be used by __iter__ or __getitem__
        """
        for node_data in data:
            yield self._make_instance(node_data)
        for node in self.node_stack:
            yield node

    def _make_instance(self, node_data):
        clone = self.__class__(**node_data)
        clone._is_item = True
        for name in self._nodes:
            _name = un_camel(name)
            if _name in node_data:  # check for partial data
                getattr(clone, name)._load_data(node_data[_name])
        cache = node_data.get('_cache', {})
        for name, model in self._linked_models.items():
            _name = un_camel(name)
            if _name in cache:
                ins = model(cache[_name])
                ins.key = cache[_name]['key']
                ins.set_data(cache[_name])
                setattr(clone, name, ins)
        self.node_stack.append(clone)
        return clone

    def clean_value(self):
        """
        populates json serialization ready data for storing on riak
        :return: [{},]
        """
        return [super(ListNode, mdl).clean_value() for mdl in self]

    def __repr__(self):
        """
        this works for two different object.
        - Main ListNode object
        - Items of the node (like instance of a class) which created on iteration of main object
        :return:
        """
        if not self._is_item:
            return [obj for obj in self[:10]].__repr__()
        else:
            try:
                u = six.text_type(self)
            except (UnicodeEncodeError, UnicodeDecodeError):
                u = '[Bad Unicode data]'
            return six.text_type('<%s: %s>' % (self.__class__.__name__, u))

    def add(self, **kwargs):
        """
        stores node data without creating an instance of it
        this is more efficient if node instance is not required
        :param kwargs: properties of the ListNode
        :return: None
        """
        self._data.append(kwargs)

    def __call__(self, **kwargs):
        """
        stores created instance in node_stack and returns it's reference to callee
        :param kwargs:
        :return:
        """
        clone = self.__class__(**kwargs)
        clone._is_item = True
        self.node_stack.append(clone)
        return clone

    def __len__(self):
        return len(self._data)

    def __getitem__(self, index):
        if self.node_stack:
            # since we create node instances on demand based,
            # mixing the output of generator with content of node_stack can cause a confusion
            # so it's safer to prevent this -hopefully- rarely needed usage
            raise RuntimeError("Can't slice a modified NodeList")
        if isinstance(index, int):
            return self._make_instance(self._data.pop(index))
        elif isinstance(index, slice):
            data_slice = self._data.__getitem__(index)
            self._data = self._data[:slice.start] + self._data[slice.stop:]
            return self._generate_instances(data_slice)
        else:
            raise TypeError("index must be int or slice")

    def __iter__(self):
        return self._generate_instances(self._data)

        # def __setitem__(self, key, value):
        #     self.values[key] = value

        # def __delitem__(self, key):
        #     del self.values[key]
