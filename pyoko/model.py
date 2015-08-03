# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from collections import defaultdict
from datetime import datetime
from six import add_metaclass
import six
from pyoko import field
from pyoko.conf import settings
from pyoko.db.base import DBObjects
from pyoko.lib.utils import un_camel, un_camel_id
import weakref
import lazy_object_proxy


class LinkModel(object):
    _TYPE = 'Proxy'

    def __init__(self, model, one_to_one=False, **kwargs):
        self.model = model
        self.is_one_to_one = one_to_one
        self.kwargs = kwargs


# class LinkModelProxy(object):
#     # TODO: this isn't nice, brake's introspection in ipython etc
#     def __init__(self, model, name, o2o, parent):
#         self.model = model
#         self.name = name
#         self.o2o = o2o
#         self.parent = parent
#
#     def __getattr__(self, item):
#         model = self.model(self.o2o)
#         setattr(self.parent, self.name, model)
#         return getattr(model, item)

# region ModelMeta and Registry
class Registry(object):
    def __init__(self):
        self.registry = []
        self.link_registry = defaultdict(list)
        self.back_link_registry = defaultdict(list)


    def register_model(self, klass):
        if klass not in self.registry:
            # register model to base registry
            self.registry += [klass]
            klass_name = un_camel(klass.__name__)
            self.process_many_to_many(klass, klass_name)
            for name, (
            linked_model, is_one_to_one) in klass._linked_models.items():
                # register models that linked from this model
                self.link_registry[linked_model].append((name, klass))
                # register models that gives (back)links to this model
                self.back_link_registry[klass].append((name, klass_name,
                                                     linked_model))
                if is_one_to_one:
                    self._process_one_to_one(klass, klass_name, linked_model)
                else:
                    self._process_one_to_many(klass, klass_name, linked_model)

    def process_many_to_many(self, klass, klass_name):
        for node in klass._nodes.values():
            if node._linked_models:
                for (model, is_o2o) in node._linked_models.values():
                    klass._many_to_models.append(model)
                    self._process_one_to_many(klass, klass_name, model)


    def _process_one_to_one(self, klass, klass_name, linked_model):
        klass_instance = klass(one_to_one=True)
        klass_instance._is_auto_created_reverse_link = True
        for instance_ref in linked_model._instance_registry:
            mdl = instance_ref()
            if mdl:  # if not yet garbage collected
                setattr(mdl, klass_name, klass_instance)
        linked_model._linked_models[klass_name] = (klass, True)

    def _process_one_to_many(self, klass, klass_name, linked_model):
        # other side of n-to-many should be a ListNode
        # named with a "_set" suffix and
        # our linked_model as the sole element
        set_name = '%s_set' % klass_name
        # create a new class which extends ListNode
        klass_instance = klass()
        klass_instance._is_auto_created_reverse_link = True
        listnode = type(set_name,
                        (ListNode,),
                        {klass_name: klass_instance})
        listnode._linked_models[klass_name] = (klass, False)
        linked_model._nodes[set_name] = listnode
        # add just created model_set to already initialised instances
        for instance_ref in linked_model._instance_registry:
            mdl = instance_ref()
            if mdl: # if not yet garbage collected
                mdl._instantiate_node(set_name, listnode)

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

    def __new__(mcs, name, bases, attrs):
        base_model_class = bases[0]
        class_type = getattr(base_model_class, '_TYPE', None)
        if class_type == 'Model':
            mcs.process_models(attrs, base_model_class)
        if class_type == 'ListNode':
            mcs.process_listnode(attrs, base_model_class)
        mcs.process_attributes(attrs)
        new_class = super(ModelMeta, mcs).__new__(mcs, name, bases, attrs)
        return new_class

    @staticmethod
    def process_listnode(attrs, base_model):
        attrs['idx'] = field.Id()

    @staticmethod
    def process_attributes(attrs):
        """
        we're iterating over attributes of the soon to be created class object.
        :param dict attrs: attribute dict
        """
        attrs['_nodes'] = {}
        attrs['_linked_models'] = {}  # property_name: (model, is_one_to_one)
        attrs['_fields'] = {}
        attrs['_many_to_models'] = []

        for key, attr in list(attrs.items()):
            # if it's a class (not instance) and it's type is Node
            if hasattr(attr, '__base__') and getattr(attr.__base__,
                                                     '_TYPE', '') in ['Node', 'ListNode']:
                attrs['_nodes'][key] = attrs.pop(key)
            else:  # otherwise it should be a field or linked model
                attr_type = getattr(attr, '_TYPE', '')
                if attr_type == 'Model':
                    linked_model_instance = attrs.pop(key)
                    attrs['_linked_models'][key] = (
                        linked_model_instance.__class__,
                        linked_model_instance._is_one_to_one)
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
        attrs['_instance_registry'] = set()
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
        self.timer = 0.0
        self.path = []
        self._parent = None
        self._field_values = {}
        self._instantiate_linked_models()
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
    # def __getattr__(self, item):
    #     if item in self._linked_models:
    #         mdl = self._linked_models[item][0]()
    #         setattr(self, item, mdl)
    #         return mdl
    #     else:
    #         raise AttributeError

    def _instantiate_linked_models(self):
        for name, (mdl, o2o) in self._linked_models.items():
            # setattr(self, name, LinkModelProxy(mdl, name, o2o, self))
            setattr(self, name, lazy_object_proxy.Proxy(mdl))

    def _instantiate_node(self, name, klass):
        # instantiate given node, pass path data
        ins = klass()
        ins.path = self.path + [self.__class__.__name__.lower()]
        setattr(self, name, ins)

    def _instantiate_nodes(self):
        """
        instantiate all nodes
        """
        for name, klass in self._nodes.items():
            self._instantiate_node(name, klass)
            # if self._nodes:
            #     print("INS NODE: ", self, self._nodes)

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

        for name, _field in self._fields.items():
            if name in kwargs:
                val = kwargs.get(name, self._field_values.get(name))
                if not kwargs.get('from_db'):
                    setattr(self, name, val)
                else:
                    _field._load_data(self, val)

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
        multi = in_multi or isinstance(self, ListNode)
        for name in self._linked_models:
            # obj = getattr(self, name) ### obj.has_many_values()
            result.append((un_camel_id(name), 'string', True, True, multi))

        for name, field_ins in self._fields.items():
            field_name = self._path_of(name).replace(model_name + '.', '')
            result.append((field_name,
                           field_ins.solr_type,
                           field_ins.index,
                           field_ins.store,
                           multi))
        for mdl_ins in self._nodes:
            result.extend(
                getattr(self, mdl_ins)._collect_index_fields(model_name,
                                                             multi))
        return result

    def _load_data(self, data, from_db=False):
        """
        With the data returned from riak:
        - fills model's fields, nodes and listnodes
        - instantiates linked model instances
        :type bool from_db: if data coming from db instead of calling
        self._set_fields_values() we simply use field's _load_data method.
        :param dict data:
        :return: self
        """
        self._data = data.copy()
        for name in self._nodes:
            _name = un_camel(name)
            if _name in self._data:
                new = getattr(self, name).__class__()
                new._load_data(self._data[_name], from_db)
                setattr(self, name, new)
        self._data['from_db'] = from_db
        self._set_fields_values(self._data)
        return self

    # ######## Public Methods  #########

    def clean_value(self, root_obj_key=None):
        """
        generates a json serializable representation of the model data
        :rtype: dict
        :return: riak ready python dict
        """
        dct = {}
        if root_obj_key is None:
            root_obj_key = self.key

        # get values of nodes
        for name in self._nodes:
            dct[un_camel(name)] = getattr(self, name).clean_value(root_obj_key)

        # get vales of linked models
        if self._linked_models:
            dct['_cache'] = {}
            for name in self._linked_models:
                link_mdl = getattr(self, name)
                _name = un_camel(name)
                dct[un_camel_id(name)] = link_mdl.key or ''
                if (link_mdl.key and not link_mdl._is_auto_created_reverse_link):
                    if root_obj_key is None or link_mdl.key != root_obj_key:
                        dct['_cache'][_name] = link_mdl.clean_value(root_obj_key)
                    else:
                        dct['_cache'][_name]={}
                    dct['_cache'][_name]['key'] = link_mdl.key

        # get values of fields
        for name, field_ins in self._fields.items():
            dct[un_camel(name)] = field_ins.clean_value(
                self._field_values.get(name))
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
    _SEARCH_INDEX = ''

    @classmethod
    def get_search_index(cls):
        if not cls._SEARCH_INDEX:
            cls._SEARCH_INDEX = settings.get_index(cls._get_bucket_name())
        return cls._SEARCH_INDEX

    def __init__(self, context=None, **kwargs):
        self._riak_object = None
        self.key = None
        self._instance_registry.add(weakref.ref(self))
        self.context = context or {}
        self.row_level_access()
        # self._prepare_linked_models()
        self._is_one_to_one = kwargs.pop('one_to_one', False)
        self.title = kwargs.pop('title', self.__class__.__name__)
        super(Model, self).__init__(**kwargs)
        self.objects.model = self
        self.objects.model_class = self.__class__

    def set_data(self, data, from_db=False):
        """
        first calls supers load_data
        then fills linked models

        :param from_db: if data coming from db then we will
        use related field type's _load_data method
        :param data: data
        :return:
        """
        self._load_data(data, from_db)
        cache = data.get('_cache', {})
        if cache:
            for name in self._linked_models:
                _name = un_camel(name)
                if _name in cache:
                    mdl = getattr(self, name)
                    mdl.key = cache[_name]['key']
                    mdl.set_data(cache[_name], from_db)
        return self



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

    def _save_many_models(self):
        """
        add/update self on linked models from our listnodes
        """
        for mdl in self._many_to_models:
            id_name = un_camel_id(self.__class__.__name__)
            for obj in mdl.objects.filter(**{id_name: self.key}):
                set_name = "%s_set" % un_camel(self.__class__.__name__)
                obj_set = getattr(obj, set_name)
                obj_set.update_linked_model(self)
                obj.save()

    def _save_backlinked_models(self):
        # TODO: when called from a deleted object, instead of
        # updating we should remove it from target
        self._save_many_models()
        for name, mdl in self._get_reverse_links():
            for obj in mdl.objects.filter(**{un_camel_id(name): self.key}):
                setattr(obj, name, self)
                # obj.save()
                obj.save(dont_save_backlinks=True)
        for pointer, name, mdl in self._get_forward_links():
            obj = mdl.objects.get(getattr(self, pointer).key)
            back_linking_model = getattr(obj, name, None)
            if back_linking_model:
                is_auto_created = getattr(obj, name,
                                          None)._is_auto_created_reverse_link
                setattr(obj, name, self)
                obj.save(dont_save_backlinks=is_auto_created)
            else:
                object_set = getattr(obj, '%s_set' % name)
                object_set.add(**{name: self})
                obj.save(dont_save_backlinks=True)

    def delete(self):
        self.deleted = True
        self.save()


class ListNode(Node):
    """
    Currently we disregard the ordering when updating items of a ListNode
    """
    # HASH_BY = '' # calculate __hash__ value by field defined here
    _TYPE = 'ListNode'

    def __init__(self, **kwargs):
        self._is_item = False
        self._from_db = False
        self.values = []
        self.node_stack = []
        self._data = []
        super(ListNode, self).__init__(**kwargs)

    # ######## Public Methods  #########

    def update_linked_model(self, model_ins):
        for name, (mdl, o2o) in self._linked_models.items():
            if model_ins.__class__ == mdl:
                for item in self:
                    if getattr(item, name).key == model_ins.key:
                        self.node_stack.pop()
                        self.node_stack.append(model_ins)


    def _load_data(self, data, from_db=False):
        """
        just stores the data at self._data, actual object creation done at _generate_instances()
        """
        self._data = data
        self._from_db = from_db

    def _generate_instances(self):
        """
        a clone generator that will be used by __iter__ or __getitem__
        """
        for node in self.node_stack:
            yield node
        while self._data:
            yield self._make_instance(self._data.pop(0))

    def _make_instance(self, node_data):

        node_data['from_db'] = self._from_db
        clone = self.__call__(**node_data)
        clone._is_item = True
        for name in self._nodes:
            _name = un_camel(name)
            if _name in node_data:  # check for partial data
                getattr(clone, name)._load_data(node_data[_name])
        cache = node_data.get('_cache', {})
        for name, (model, is_one_to_one) in self._linked_models.items():
            _name = un_camel(name)
            if _name in cache:
                ins = model()
                ins(**cache[_name])
                ins.key = cache[_name]['key']
                ins.set_data(cache[_name], self._from_db)
                setattr(clone, name, ins)
        # self.node_stack.append(clone)
        return clone

    def clean_value(self, root_obj_key):
        """
        populates json serialization ready data for storing on riak
        :return: [{},]
        """
        return [super(ListNode, mdl).clean_value(root_obj_key) for mdl in self]

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

    # def __hash__(self):
    #     if self.HASH_BY:
    #         return hash(getattr(self, self.HASH_BY))

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
        return list(self._generate_instances()).__getitem__(index)

    def __iter__(self):
        return self._generate_instances()

        # def __setitem__(self, key, value):
        #     self.values[key] = value

        # def __delitem__(self, key):
        #     del self.values[key]
