# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from collections import defaultdict
from copy import copy
import datetime
import logging
from uuid import uuid4
from six import add_metaclass
import six
from . import fields as field
from .conf import settings
from .db.base import DBObjects
from .lib.utils import un_camel, un_camel_id, lazy_property, pprnt, get_object_from_path
import weakref
import lazy_object_proxy


class LazyModel(lazy_object_proxy.Proxy):
    key = None

    def __init__(self, wrapped):
        super(LazyModel, self).__init__(wrapped)


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
        self.lazy_models = {}
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
                kls_name = '%s_set' % klass_name if not is_one_to_one else klass_name
                self.link_registry[linked_model].append((name, klass, klass_name, kls_name))
                # register models that gives (back)links to this model
                self.back_link_registry[klass].append((name, klass_name, linked_model))
                if is_one_to_one:
                    self._process_one_to_one(klass, klass_name, linked_model)
                else:
                    self._process_one_to_many(klass, klass_name, linked_model)

    def _process_many_to_many(self, klass, klass_name):
        for node in klass._nodes.values():
            if node._linked_models:
                for name, (model, is_one_to_one) in node._linked_models.items():
                    if not is_one_to_one:
                        self.link_registry[model].append((name, klass, klass_name,
                                                          '%s_set' % klass_name))
                    else:
                        self.link_registry[model].append((name, klass, klass_name, klass_name))
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

        mcs.process_attributes(attrs, name)
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
    def process_attributes(attrs, model_name):
        """
        we're iterating over attributes of the soon to be created class object.

        :param dict attrs: attribute dict
        """
        attrs['_nodes'] = {}
        attrs['_linked_models'] = {}  # property_name: (model, is_one_to_one)
        attrs['_lazy_linked_models'] = {}  # property_name: (model, is_one_to_one)
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
                elif attr_type == 'Link':
                    lazy_link = attrs.pop(key)
                    attrs['_lazy_linked_models'][key] = (lazy_link.link_to, lazy_link.one_to_one)
                    model_registry.lazy_models[lazy_link.link_to] = (key, lazy_link.one_to_one)

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
                        'list_fields': [],
                        'list_filters': [],
                        'search_fields': [],
                        }
        if 'Meta' not in attrs:
            attrs['Meta'] = type('Meta', (object,), DEFAULT_META)
        else:
            for k, v in DEFAULT_META.items():
                if k not in attrs['Meta'].__dict__:
                    setattr(attrs['Meta'], k, v)


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
        self.set_tmp_key()
        try:
            self.root
        except:
            self.root = kwargs.pop('root', None)
        self.context = kwargs.pop('context', None)
        self._field_values = {}
        self._data = {}
        self._choice_fields = []
        self._choices_manager = get_object_from_path(settings.CATALOG_DATA_MANAGER)

        # if model has cell_filters that applies to current user,
        # filtered values will be kept in _secured_data dict
        self._secured_data = {}

        # linked models registry for finding the list_nodes that contains a link to us
        self._model_in_node = defaultdict(list)

        # a registry for -keys of- models which processed with clean_value method
        # this is required to prevent endless recursive invocation of n-2-n related models
        self.processed_nodes = kwargs.pop('processed_nodes', [])

        self._instantiate_linked_models(kwargs)
        self._instantiate_nodes()
        self._set_fields_values(kwargs)

    @lazy_property
    def _ordered_fields(self):
        return sorted(self._fields.items(), key=lambda kv: kv[1]._order)

    def set_tmp_key(self):
        self.key = "TMP_%s_%s" % (self.__class__.__name__, uuid4().hex[:10])

    @classmethod
    def _get_bucket_name(cls):
        return getattr(cls.Meta, 'bucket_name', un_camel(cls.__name__))

    def _path_of(self, prop):
        """
        returns the dotted path of the given model attribute
        """
        root = self.root or self
        return ('.'.join(list(self.path + [un_camel(self.__class__.__name__),
                                           prop]))).replace(root._get_bucket_name() + '.', '')

    def _instantiate_linked_models(self, data=None):
        def foo_model(modl, context):
            return LazyModel(lambda: modl(context))
        for name, (mdl, o2o) in self._linked_models.items():
            # for each linked model

            if data:
                # data can be came from db or user
                if name in data and isinstance(data[name], Model):
                    # this should be user, and it should be a model instance
                    linked_mdl_ins = data[name]
                    setattr(self, name, linked_mdl_ins)
                    if self.root.is_in_db():
                        # if root model already saved (has a key),
                        # update reverse relations of linked model
                        self.root.update_new_linked_model(linked_mdl_ins, name, o2o)
                    else:
                        # otherwise we should do it after root model saved
                        self.root.new_back_links.append((linked_mdl_ins, name, o2o))
                else:
                    id_name = un_camel_id(name)
                    if id_name in data and data[id_name] is not None:
                        # this is coming from db,
                        # we're preparing a lazy model loader
                        def fo(modl, context, key):
                            return lambda: modl(context).objects.get(key)
                        obj = LazyModel(fo(mdl, self.context, data[id_name]))
                        obj.key = data[id_name]
                        setattr(self, name, obj)
                    else:
                        # creating an lazy proxy for empty linked model
                        # Note: this should be explicitly saved before root model!
                        setattr(self, name, foo_model(mdl, self.context))
                        # setattr(self, name, LazyModel((lambda: lambda: mdl(self.context))()))
            else:
                # creating an lazy proxy for empty linked model
                # Note: this should be explicitly saved before root model!
                setattr(self, name, foo_model(mdl, self.context))
                # setattr(self, name, LazyModel((lambda: lambda: mdl(self.context))()))

    def _instantiate_node(self, name, klass):
        # instantiate given node, pass path and root info
        ins = klass(**{'context': self.context,
                       'root': self.root or self})
        ins.path = self.path + [self.__class__.__name__.lower()]
        setattr(self, name, ins)
        return ins

    def _instantiate_nodes(self):
        """
        instantiate all nodes
        """
        for name, klass in self._nodes.items():
            self._instantiate_node(name, klass)

    def _fill_nodes(self, data):
        for name in self._nodes:
            _name = un_camel(name)
            if _name in self._data:
                # node = self._instantiate_node(name, getattr(self, name).__class__)
                node = getattr(self, name)
                node._load_data(self._data[_name], data['from_db'])

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

    def get_humane_value(self, name):
        if name in self._choice_fields:
            return getattr(self, 'get_%s_display' % name)()
        else:
            val = getattr(self, name)
            if isinstance(val, datetime.datetime):
                return val.strftime(settings.DATETIME_DEFAULT_FORMAT or field.DATE_TIME_FORMAT)
            elif isinstance(val, datetime.date):
                return val.strftime(settings.DATE_DEFAULT_FORMAT or field.DATE_FORMAT)
            else:
                return val

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
                    root = self.root or self
                    if path_name in root.get_unpermitted_fields():
                        self._secured_data[path_name] = val
                        continue
                    if not kwargs.get('from_db'):
                        setattr(self, name, val)
                    else:
                        _field._load_data(self, val)
                    if _field.choices is not None:
                        self._choice_fields.append(name)

                        # adding get_%s_display() methods for fields which has "choices" attribute
                        def foo():
                            choices, value = copy(_field.choices), copy(val)
                            return lambda: self._choices_manager(choices, value)

                        setattr(self, 'get_%s_display' % name, foo())

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
            result.append((un_camel_id(name), 'string', True, False, multi))

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
        self._data['from_db'] = from_db
        self._fill_nodes(self._data)
        self._set_fields_values(self._data)
        self._instantiate_linked_models(self._data)
        return self

    def _clean_node_value(self, dct):
        # get values of nodes
        for name in self._nodes:
            node = getattr(self, name)
            node.processed_nodes = self.processed_nodes
            dct[un_camel(name)] = node.clean_value()
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
            lnkd_mdl = getattr(self, name)
            dct[un_camel_id(name)] = lnkd_mdl.key if lnkd_mdl else None

    def clean_field_values(self):
        return dict((un_camel(name), field_ins.clean_value(self._field_values.get(name)))
                    for name, field_ins in self._fields.items())

    def clean_value(self):
        """
        generates a json serializable representation of the model data
        :rtype: dict
        :return: riak ready python dict
        """
        dct = {}
        self._clean_field_value(dct)
        self._clean_node_value(dct)
        self._clean_linked_model_value(dct)
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

        self.unpermitted_fields = []
        self.is_unpermitted_fields_set = False
        self.context = context

        self._pass_perm_checks = kwargs.pop('_pass_perm_checks', False)
        # if not self._pass_perm_checks:
        #     self.row_level_access(context)
        #     self.apply_cell_filters(context)
        self.objects._pass_perm_checks = self._pass_perm_checks
        # self._prepare_linked_models()
        self._is_one_to_one = kwargs.pop('one_to_one', False)
        # TODO : Remove self.title if not neccessary or prefix with _
        self.title = kwargs.pop('title', self.__class__.__name__)
        self.root = self
        self.new_back_links = []
        kwargs['context'] = context
        super(Model, self).__init__(**kwargs)

        self.objects.set_model(model=self)
        self._instance_registry.add(weakref.ref(self))
        self.saved_models = []

    def prnt(self):
        try:
            pprnt(self._data)
        except:
            pprnt(self.clean_value())

    def __eq__(self, other):
        return self._data == other._data and self.key == other.key

    def __hash__(self):
        return hash(self.key)

    def is_in_db(self):
        """
        is this model stored to db
        :return:
        """
        return self.key and not self.key.startswith('TMP_')

    def get_choices_for(self, field):

        choices = self._fields[field].choices
        if isinstance(choices, six.string_types):
            return self._choices_manager.get_all(choices)
        else:
            return choices

    @classmethod
    def get_search_index(cls):
        if not cls._SEARCH_INDEX:
            # cls._SEARCH_INDEX = settings.get_index(cls._get_bucket_name())
            cls._SEARCH_INDEX = cls.objects.bucket.get_property('search_index')
        return cls._SEARCH_INDEX

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
        return self

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

    def update_new_linked_model(self, linked_mdl_ins, name, is_one_to_one):
        for (local_field_name, kls, remote_field_name, remote_name
             ) in linked_mdl_ins._get_reverse_links():
            if local_field_name == name and isinstance(self, kls):
                if not is_one_to_one:
                    remote_set = getattr(linked_mdl_ins, remote_name)
                    if self not in remote_set:
                        remote_set(**{remote_field_name: self.root})
                        linked_mdl_ins.save()
                else:
                    setattr(linked_mdl_ins, remote_name, self.root)
                    linked_mdl_ins.save()

    def save(self):
        self.objects.save_model(self)
        for i in range(len(self.new_back_links)):
            if self.new_back_links:
                self.update_new_linked_model(*self.new_back_links.pop())
        return self

    def delete(self):
        """
        this method just flags the object as "deleted" and saves it to db
        """
        self.deleted = True
        self.save()


class LinkProxy(object):
    _TYPE = 'Link'

    def __init__(self, link_to, one_to_one=False, verbose_name=None, reverse_name=None):
        self.link_to = link_to
        self.one_to_one = one_to_one
        self.verbose_name = verbose_name
        self.reverse_name = reverse_name


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
        self.node_dict = {}
        super(ListNode, self).__init__(**kwargs)

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
        while self._data:
            yield self._make_instance(self._data.pop(0))

    def _make_instance(self, node_data):
        """
        create a ListNode instance from node_data

        :param dict node_data:
        :return: ListNode item
        """
        node_data['from_db'] = self._from_db
        clone = self.__call__(**node_data)
        clone.container = self
        clone._is_item = True
        for name in self._nodes:
            _name = un_camel(name)
            if _name in node_data:  # check for partial data
                getattr(clone, name)._load_data(node_data[_name])
        for name, (model, is_one_to_one) in self._linked_models.items():
            _name = un_camel_id(name)
            ins = getattr(clone, name)
            # ins.key = node_data[_name]
            self.node_dict[ins.key] = clone
            break  # only one linked_model can represent an item
        # self.node_stack.append(clone)
        return clone

    def clean_value(self):
        """
        populates json serialization ready data for storing on riak
        :return: [{},]
        """
        result = []
        for mdl in self:
            # mdl.processed_nodes = self.processed_nodes
            result.append(super(ListNode, mdl).clean_value())
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
        self._data.append(kwargs)

    def __call__(self, **kwargs):
        """
        stores created instance in node_stack and returns it's reference to callee
        :param kwargs:
        :return:
        """
        kwargs['root'] = self.root
        clone = self.__class__(**kwargs)
        # clone.root = self.root
        clone._is_item = True
        clone.processed_nodes = self.root.processed_nodes
        self.node_stack.append(clone)
        return clone

    def clear(self):
        """
        clear outs the list node
        """
        if self._is_item:
            raise TypeError("This an item of the parent ListNode")
        self.node_stack = []
        self._data = []

    def __contains__(self, item):
        if self._data:
            return any([d[un_camel_id(item.__class__.__name__)] == item.key for d in self._data])
        else:
            return item.key in self.node_dict

    def __len__(self):
        return len(self._data or self.node_stack)

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
