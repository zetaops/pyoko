# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from collections import defaultdict
from datetime import datetime
import logging
from uuid import uuid4
from six import add_metaclass
import six
from pyoko import field
from pyoko.conf import settings
from pyoko.db.base import DBObjects
from pyoko.lib.utils import un_camel, lazy_property, pprnt
import weakref
import lazy_object_proxy

# FIXME: added for speedup the debugging, remmeber to remove
import sys

sys.setrecursionlimit(300)


# log = logging.getLogger(__name__)
# fh = logging.FileHandler(filename="/tmp/pyoko.log", mode="w")
# fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
# log.addHandler(fh)
# log.setLevel(logging.INFO)
class FakeContext(object):
    """
    this fake context object can be used to use
    ACL limited models from shell
    """

    def has_permission(self, perm):
        return True


super_context = FakeContext()


class Registry(object):
    def __init__(self):
        self.registry = {}
        self.app_registry = defaultdict(dict)
        self.link_registry = defaultdict(list)
        self.back_link_registry = defaultdict(list)

    def register_model(self, klass):
        if klass not in self.registry:
            # register model to base registry
            self.registry[klass.__name__] = klass
            self.app_registry[klass.Meta.app][klass.__name__] = klass
            klass_name = un_camel(klass.__name__)
            self._process_many_to_many(klass, klass_name)
            for name, (linked_model, is_one_to_one) in klass._linked_models.items():
                # register models that linked from this model
                self.link_registry[linked_model].append((name, klass))
                # register models that gives (back)links to this model
                self.back_link_registry[klass].append((name, klass_name, linked_model))
                if is_one_to_one:
                    self._process_one_to_one(klass, klass_name, linked_model)
                else:
                    self._process_one_to_many(klass, klass_name, linked_model)

    def _process_many_to_many(self, klass, klass_name):
        for node in klass._nodes.values():
            if node._linked_models:
                for (model, is_one_to_one) in node._linked_models.values():
                    # klass._many_to_models.append(model)
                    self._process_one_to_many(klass, klass_name, model)

    def _process_one_to_one(self, klass, klass_name, linked_model):
        klass_instance = klass(one_to_one=True)
        klass_instance._is_auto_created = True
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
        klass_instance._is_auto_created = True
        listnode = type(set_name, (ListNode,),
                        {klass_name: klass_instance, '_is_auto_created': True})
        listnode._linked_models[klass_name] = (klass, False)
        linked_model._nodes[set_name] = listnode
        # add just created model_set to model instances that
        # initialized inside of another model as linked model
        for instance_ref in linked_model._instance_registry:
            mdl = instance_ref()
            if mdl:  # if not yet garbage collected
                mdl._instantiate_node(set_name, listnode)

    def get_base_models(self):
        return self.registry.values()

    def get_apps(self):
        return self.app_registry.keys()

    def get_models_by_apps(self):
        return [(app_names, model_dict.values())
                for app_names, model_dict in self.app_registry.items()]

    def get_model(self, model_name):
        return self.registry[model_name]

    def get_models_of_app(self, app_name):
        return self.app_registry[app_name].values()


model_registry = Registry()


# noinspection PyMissingConstructor
class ModelMeta(type):
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

    def __init__(mcs, name, bases, attrs):
        if mcs.__name__ not in ('Model', 'Node', 'ListNode'):
            ModelMeta.process_objects(mcs)
        if mcs.__base__.__name__ == 'Model':
            # add models to model_registry
            mcs.objects = DBObjects(model_class=mcs)
            model_registry.register_model(mcs)
            if 'bucket_name' not in mcs.Meta.__dict__:
                mcs.Meta.bucket_name = un_camel(mcs.__name__)

    @staticmethod
    def process_listnode(attrs, base_model):
        attrs['idx'] = field.Id()

    @staticmethod
    def process_objects(kls):
        # first add a Meta object if not exists
        if 'Meta' not in kls.__dict__:
            kls.Meta = type('Meta', (object,), {})
        # set verbose_name(s) if not already set
        if 'verbose_name' not in kls.Meta.__dict__:
            kls.Meta.verbose_name = kls.__name__
        if 'verbose_name_plural' not in kls.Meta.__dict__:
            kls.Meta.verbose_name_plural = kls.Meta.verbose_name + 's'

    @staticmethod
    def process_attributes(attrs):
        """
        we're iterating over attributes of the soon to be created class object.

        :param dict attrs: attribute dict
        """
        attrs['_nodes'] = {}
        attrs['_linked_models'] = {}  # property_name: (model, is_one_to_one)
        attrs['_fields'] = {}
        # attrs['_many_to_models'] = []

        for key, attr in list(attrs.items()):
            # if it's a class (not instance) and it's type is Node or ListNode
            if hasattr(attr, '__base__') and getattr(attr.__base__, '_TYPE', '') in ['Node',
                                                                                     'ListNode']:
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
        DEFAULT_META = {'bucket_type': settings.DEFAULT_BUCKET_TYPE,
                        'field_permissions': {},
                        'app': 'main',
                        'list_fields': []}
        if 'Meta' not in attrs:
            attrs['Meta'] = type('Meta', (object,), DEFAULT_META)
        else:
            for k, v in DEFAULT_META.items():
                if k not in attrs['Meta'].__dict__:
                    attrs['Meta'].__dict__[k] = v


@add_metaclass(ModelMeta)
class Node(object):
    """
    We store node classes in _nodes[] attribute at ModelMeta,
    then replace them with their instances at _instantiate_nodes()

    Likewise we store linked models in _linked_models[]

    Since fields are defined as descriptors,
    they can access to instance they called from but to
    access their methods and attributes,
    we're copying fields themself into self._fields[] attribute.
    So, we get values of fields from self._field_values[]
    and access to fields themselves from self._fields[]

    """
    _TYPE = 'Node'
    _is_auto_created = False

    def __init__(self, **kwargs):
        super(Node, self).__init__()
        self.timer = 0.0
        self.path = []
        self.set_key(kwargs)
        self.parent = kwargs.pop('parent', self)
        self.root = kwargs.pop('root', self)

        self._field_values = {}
        # if model has cell_filters that applies to current user,
        # filtered values will be kept in _secured_data dict
        self._secured_data = {}
        # linked models registry for finding the list_nodes that contains a link to us
        self._model_in_node = defaultdict(list)
        # a registry for -keys of- models which processed with clean_value method
        # this is required to prevent endless recursive invocation of n-2-n related models
        self._instantiate_linked_models(kwargs)
        self._instantiate_nodes()
        self._set_fields_values(kwargs)

    def set_key(self, kwargs):
        self.key = kwargs.get('key', "TMP_%s_%s" % (self.__class__.__name__, uuid4().hex[:10]))

    @classmethod
    def _get_bucket_name(cls):
        return getattr(cls.Meta, 'bucket_name', un_camel(cls.__name__))

    def _path_of(self, prop):
        """
        returns the dotted path of the given model attribute
        """
        return ('.'.join(list(self.path + [un_camel(self.__class__.__name__),
                                           prop]))).replace(self.parent._get_bucket_name() + '.',
                                                            '')

    def _instantiate_linked_models(self, data=None):
        for name, (mdl, o2o) in self._linked_models.items():
            # TODO: investigate if this really required/needed and remove if not
            if data is not None and name in data:
                if isinstance(data[name], Model):
                    obj = data[name]
                    obj.root = self.root
                elif isinstance(data[name], dict):
                    obj = lazy_object_proxy.Proxy(
                        lambda: mdl(self.parent.context, root=self.root, **data[name]))
                # then it should be key of the object
                elif isinstance(data[name], six.string_types):
                    obj = lazy_object_proxy.Proxy(
                        lambda: mdl(self.parent.context, root=self.root, key=data[name]))
                else:
                    raise Exception("Unsupported data type for linked model: %s: %s" %
                                    (name, data[name]))
            else:
                obj = lazy_object_proxy.Proxy(lambda: mdl(self.parent.context, root=self.root))
            setattr(self, name, obj)

    def _instantiate_node(self, name, klass):
        # instantiate given node, pass path and parent info
        ins = klass(**{'parent': self.parent, 'root': self.root})
        ins.parent = self.parent
        ins.path = self.path + [self.__class__.__name__.lower()]
        for (mdl, o2o) in klass._linked_models.values():
            self._model_in_node[mdl].append(ins)
        setattr(self, name, ins)
        return ins

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
        """
        fill the fields of this node
        :type kwargs: builtins.dict
        """
        if kwargs:
            for name, _field in self._fields.items():
                if name in kwargs:
                    val = kwargs.get(name, self._field_values.get(name))
                    path_name = self._path_of(name)
                    # parent = self.parent or self
                    if path_name in self.parent.get_unpermitted_fields():
                        self._secured_data[path_name] = val
                        continue
                    if 'from_db' not in kwargs:
                        setattr(self, name, val)
                    else:
                        _field._load_data(self, val)
                        # for name in self._linked_models:
                        #     linked_model = kwargs.get(name)
                        #     if linked_model:
                        #         setattr(self, name, linked_model)

    def _collect_index_fields(self, in_multi=False):
        """
        collects fields which will be indexed
        :param str model_name: base Model's name
        :param bool in_multi: if we are in a ListNode or not
        :return: [(field_name, solr_type, is_indexed, is_stored, is_multi]
        """
        result = []
        # if not model_name:
        #     model_name = self._get_bucket_name()
        multi = in_multi or isinstance(self, ListNode)
        for name in self._linked_models:
            # obj = getattr(self, name) ### obj.has_many_values()
            result.append((un_camel(name), 'string', True, False, multi))

        for name, field_ins in self._fields.items():
            field_name = self._path_of(name)
            result.append((field_name,
                           field_ins.solr_type,
                           field_ins.index,
                           field_ins.store,
                           multi))
        for mdl_ins in self._nodes:
            result.extend(
                getattr(self, mdl_ins)._collect_index_fields(multi))
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
                new = self._instantiate_node(name, getattr(self, name).__class__)
                # new = getattr(self, name).__class__(**{})
                new._load_data(self._data[_name], from_db)
                # setattr(self, name, new)
        self._data['from_db'] = from_db
        self._set_fields_values(self._data)
        return self

    def clean_field_values(self):
        """
        :return: all fields with values as a dict.
        """
        return dict((un_camel(name), field_ins.clean_value(self._field_values.get(name)))
                    for name, field_ins in self._fields.items())

    def _clean_node_value(self, dct):
        # get values of nodes
        for name in self._nodes:
            node = getattr(self, name)
            dct[un_camel(name)] = node._clean_value()
        return dct

    def _clean_field_value(self, dct):
        # get values of fields
        for name, field_ins in self._fields.items():
            path_name = self._path_of(name)
            if path_name in self._secured_data:
                dct[un_camel(name)] = self._secured_data[path_name]
            else:
                dct[un_camel(name)] = field_ins.clean_value(self._field_values.get(name))
        return dct

    def _clean_linked_model_value(self, dct):
        # get vales of linked models
        for name in self._linked_models:
            link_mdl = getattr(self, name)
            # print(link_mdl, link_mdl.key)
            if link_mdl.is_in_db():
                # link_mdl.parent = self.parent
                if link_mdl.key not in self.parent.model_cache:
                    self.parent.model_cache[link_mdl.key] = link_mdl._clean_value()
                if self.root != self and self.root != self.parent:
                    self.root.model_cache[link_mdl.key] = link_mdl._clean_value()
                dct[name] = link_mdl.key
            else:
                dct[name] = ""

    def _clean_value(self):
        dct = {}
        self._clean_field_value(dct)
        self._clean_node_value(dct)
        if self._linked_models:
            self._clean_linked_model_value(dct)
        return dct

    def clean_value(self):
        """
        generates a json serializable representation of the model data
        :rtype: dict
        :return: riak ready python dict
        """
        dct = self._clean_value()
        dct['model_cache'] = self.model_cache
        return dct


class Model(Node):
    objects = DBObjects
    _TYPE = 'Model'

    _DEFAULT_BASE_FIELDS = {
        'timestamp': field.TimeStamp(),
        'deleted': field.Boolean(default=False, index=True)}
    _SEARCH_INDEX = ''

    def __init__(self, context=None, **kwargs):
        self._riak_object = None
        self._instance_registry.add(weakref.ref(self))
        self.unpermitted_fields = []
        self.is_unpermitted_fields_set = False
        self.context = context
        self.model_cache = {}
        self._pass_perm_checks = kwargs.pop('_pass_perm_checks', False)
        self.objects._pass_perm_checks = self._pass_perm_checks
        self._is_one_to_one = kwargs.pop('one_to_one', False)
        self.title = kwargs.pop('title', self.__class__.__name__)
        super(Model, self).__init__(**kwargs)
        self.objects.set_model(model=self)
        self._data = {}
        self.saved_models = []

    def is_saved(self, mdl):
        return mdl.key in self.saved_models

    def add_to_saved(self, mdl):
        self.saved_models.append(mdl.key)

    def prnt(self):
        pprnt(self._data or self.clean_value())

    def is_in_db(self):
        """
        is this model stored to db
        :return:
        """
        return self.key and not self.key.startswith('TMP_')

    @classmethod
    def get_search_index(cls):
        if not cls._SEARCH_INDEX:
            # cls._SEARCH_INDEX = settings.get_index(cls._get_bucket_name())
            try:
                cls._SEARCH_INDEX = cls.objects.bucket.get_property('search_index')
            except KeyError:
                print("This model probably not migrated yet: %s" % cls.__name__)
                print(cls.objects.bucket)
                print(cls.objects.bucket.get_properties())
                raise
        return cls._SEARCH_INDEX

    def set_data(self, data, from_db=False):
        """
        :param from_db: if data coming from db then we will
        use related field type's _load_data method
        :param data: data
        :return:
        """
        self._load_data(data, from_db)
        self._fill_linked_models(data, from_db)
        return self

    def _fill_linked_models(self, data, from_db):
        for name in self._linked_models:
            mdl = getattr(self, name)
            mdl.key = data[name]
            if 'model_cache' in data:
                model_cache = data['model_cache']
            else:
                model_cache = self.root._data['model_cache']
            if data[name] in model_cache:
                mdl.set_data(model_cache[mdl.key], from_db)


    def apply_cell_filters(self, context):
        self.is_unpermitted_fields_set = True
        for perm, fields in self.Meta.field_permissions.items():
            if not context.has_permission(perm):
                self.unpermitted_fields.extend(fields)
        return self.unpermitted_fields

    def get_unpermitted_fields(self):
        return (self.unpermitted_fields if self.is_unpermitted_fields_set else
                self.apply_cell_filters(self.context))

    @staticmethod
    def row_level_access(context, objects):
        """
        Define your query filters in here to enforce row level access control
        context should contain required user attributes and permissions
        eg:
            self.objects = self.objects.filter(user=context.user.key)
        """
        # FIXME: Row level access control should be enforced on cached related objects
        #  currently it's only work on direct queries
        pass

    @lazy_property
    def _name(self):
        return un_camel(self.__class__.__name)

    @lazy_property
    def _name_id(self):
        return "%s_id" % self._name

    def _get_reverse_links(self):
        """
        get models that linked from this models
        :return: [Model]
        """
        return model_registry.link_registry[self.__class__]

    def _get_forward_links(self):
        """
        get models that gives a link to to this model
        :return: [Model]
        """
        # back_link_registry has nearly same content as self._linked_models
        # TODO: refactor _linked_models to use it instead of back_link_registry
        return model_registry.back_link_registry[self.__class__]

    def save(self, root=None):
        self.root = root or self
        self.objects.save_model(self)
        self.add_to_saved(self)
        self._save_to_many_models()
        self._save_backlinked_models()
        return self

    def _save_link_models_in_list_nodes(self, node_name, lnk_mdl_name):
        """
        traverse all items of this list node
        then look for previously created reverse-list of
        list nodes which contains a link to "us" (aka: self)
        :param node_name:
        :param lnk_mdl_name:
        :return:
        """
        list_node = getattr(self, node_name)
        for item in list_node:
            linked_mdl = getattr(item, lnk_mdl_name)
            # do nothing if linked_model instance is already updated
            if not self.is_saved(linked_mdl):
                for mdl_set in linked_mdl._model_in_node[self.__class__]:
                    mdl_set.update_linked_model(self)
                linked_mdl.add_to_saved(self)
                linked_mdl.save(root=self.root)

    def _save_to_many_models(self):
        """
        add/update self on linked models from our list nodes
        """
        # traverse all nodes
        for node_name, node in self._nodes.items():
            # for each linked_model definition
            for lnk_mdl_name in node._linked_models.keys():
                self._save_link_models_in_list_nodes(node_name, lnk_mdl_name)

    def _save_backlinked_models(self):
        # FIXME: when called from a deleted object,
        # we should also remove it from target model's cache
        for name, mdl in self._get_reverse_links():
            for obj in mdl(_pass_perm_checks=True).objects.filter(**{un_camel(name): self.key}):
                if self.is_saved(obj):
                    continue
                setattr(obj, name, self)
                obj.add_to_saved(self)
                obj.save(root=self.root)
        for pointer, name, mdl in self._get_forward_links():
            cached_obj = getattr(self, pointer)
            if not cached_obj.is_in_db():
                continue
                # This is an undefined linked model slot, we just pass it
                # Currently we don't have any mechanism to enforce definition of
                # fields or linked models.
                # TODO: Add blank=False validation for fields and linked models
            obj = mdl(_pass_perm_checks=True).objects.get(cached_obj.key)
            back_linking_model = getattr(obj, name, None)
            # if obj.key in self.saved_models:
            # to prevent circular saves, but may cause missed cache updates
            # we need more tests
            # continue
            if back_linking_model:
                # this is a 1-to-1 relation
                setattr(obj, name, self)
                obj.add_to_saved(self)
                obj.save(root=self.root)
            else:
                # this is a 1-to-many relation, other side is a ListNode
                # named like object_set
                object_set = getattr(obj, '%s_set' % name)
                object_set.add(**{name: self})
                obj.add_to_saved(self)
                obj.save(root=self.root)

    def delete(self):
        """
        this method just flags the object as "deleted" and saves it to db
        """
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
        self.data = []
        self.node_dict = {}
        # print("KWARGS", kwargs, self)
        super(ListNode, self).__init__(**kwargs)

    # ######## Public Methods  #########

    def get(self, key):
        """
        this method returns the ListNode item with given "key"

        :param str key: key of the listnode item
        :return: object
        """
        if not self.node_dict:
            for node in self.node_stack:
                self.node_dict[node.key] = node
        return self.node_dict[key]

    def update_linked_model(self, model_ins):
        for name, (mdl, o2o) in self._linked_models.items():
            if model_ins.__class__ == mdl:
                for item in self:
                    if getattr(item, name).key == model_ins.key:
                        self.node_stack.remove(item)
                        break
                self.__call__(**{name: model_ins})

    def _load_data(self, data, from_db=False):
        """
        just stores the data at self._data,
        actual object creation done at _generate_instances()
        """
        self._data = data
        self.data = data[:]
        self._from_db = from_db

    def _generate_instances(self):
        """
        a clone generator that will be used by __iter__ or __getitem__
        """
        for node in self.node_stack:
            yield node
        while self.data:
            yield self._make_instance(self.data.pop(0))

    def _make_instance(self, node_data):

        node_data['from_db'] = self._from_db
        clone = self.__call__(**node_data)
        clone.container = self
        clone._is_item = True
        for name in self._nodes:
            _name = un_camel(name)
            if _name in node_data:  # check for partial data
                getattr(clone, name)._load_data(node_data[_name])
        cache = self.parent._data.get('model_cache', self.root._data['model_cache'])
        for name, (model, is_one_to_one) in self._linked_models.items():
            if name in node_data:
                key = node_data[name]
                if isinstance(key, six.string_types):
                    ins = model(root=self.root)
                    # ins._set_fields_values(from_db=self._from_db, **cache[name])
                    ins.key = key
                    ins.set_data(cache[key], self._from_db)
                else:
                    ins = key
                setattr(clone, name, ins)
        self.node_dict[clone.key] = clone
        # self.node_stack.append(clone)
        return clone

    def __call__(self, **kwargs):
        """
        stores created instance in node_stack and returns it's reference to callee
        :param kwargs:
        :return:
        """

        kwargs.update({'parent': self.parent, 'root': self.root})
        clone = self.__class__(**kwargs)
        clone._is_item = True
        self.node_stack.append(clone)
        return clone

    def _clean_value(self):
        """
        populates json serialization ready data for storing on riak
        :return: [{},]
        """
        result = []
        for mdl in self:
            result.append(super(ListNode, mdl)._clean_value())
        return result

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
        self.data.append(kwargs)

    def clear(self):
        """
        clear outs the list node
        """
        if self._is_item:
            raise TypeError("This an item of the ≠ ListNode")
        self.node_stack = []
        self.data = []

    def __len__(self):
        return len(self.data or self.node_stack)

    def __getitem__(self, index):
        return list(self._generate_instances()).__getitem__(index)

    def __iter__(self):
        return self._generate_instances()

    def __setitem__(self, key, value):
        if self._is_item:
            raise TypeError("This an item of the parent ListNode")
        self.node_stack[key] = value

    def __delitem__(self, key):
        if self._is_item:
            raise TypeError("This an item of the parent ListNode")
        self.node_stack.remove(self[key])

    def remove(self):
        """
        remove this item from list node
        note: you should save the parent object yourself.
        """
        if not self._is_item:
            raise TypeError("A ListNode cannot be deleted")
        self.container.node_stack.remove(self)
