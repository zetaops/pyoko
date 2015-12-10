# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import datetime
from copy import copy

import lazy_object_proxy
import six

from six import add_metaclass
from uuid import uuid4

from collections import defaultdict


from .conf import settings
from .lib.utils import get_object_from_path, lazy_property, un_camel, un_camel_id
from .modelmeta import ModelMeta


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

    @classmethod
    def _add_linked_model(cls, mdl, o2o=False, field=None, reverse=None, verbose=None):
        cls._linked_models[field or mdl.__name__].append({
            'o2o': o2o,
            'mdl': mdl,
            'field': field,
            'reverse': reverse,
            'verbose': verbose
        })

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
        for field_name, links in self._linked_models.items():
            for lnk in links:
                if data:
                    # data can be came from db or user
                    from .model import Model
                    if field_name in data and isinstance(data[field_name], Model):
                        # this should be coming from user,
                        # and it should be a model instance
                        linked_mdl_ins = data[field_name]
                        setattr(self, field_name, linked_mdl_ins)
                        if self.root.is_in_db():
                            # if root model already saved (has a key),
                            # update reverse relations of linked model
                            self.root.update_new_linked_model(linked_mdl_ins, field_name, lnk['o2o'])
                        else:
                            # otherwise we should do it after root model saved
                            self.root.new_back_links.append((linked_mdl_ins, field_name, lnk['o2o']))
                    else:
                        _name = un_camel_id(field_name)
                        if _name in data and data[_name] is not None:
                            # this is coming from db,
                            # we're preparing a lazy model loader
                            def fo(modl, context, key):
                                return lambda: modl(context).objects.get(key)

                            obj = LazyModel(fo(lnk['mdl'], self.context, data[_name]))
                            obj.key = data[_name]
                            setattr(self, field_name, obj)
                        else:
                            # creating an lazy proxy for empty linked model
                            # Note: this should be explicitly saved before root model!
                            setattr(self, field_name, LazyModel(lambda: lnk['mdl'](self.context)))
                else:
                    # creating an lazy proxy for empty linked model
                    # Note: this should be explicitly saved before root model!
                    setattr(self, field_name, LazyModel(lambda: lnk['mdl'](self.context)))

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
        from . import fields
        if name in self._choice_fields:
            return getattr(self, 'get_%s_display' % name)()
        else:
            val = getattr(self, name)
            if isinstance(val, datetime.datetime):
                return val.strftime(settings.DATETIME_DEFAULT_FORMAT or fields.DATE_TIME_FORMAT)
            elif isinstance(val, datetime.date):
                return val.strftime(settings.DATE_DEFAULT_FORMAT or fields.DATE_FORMAT)
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
        from .listnode import ListNode
        multi = in_multi or isinstance(self, ListNode)
        for name in self._linked_models:
            # obj = getattr(self, name) ### obj.has_many_values()
            result.append((self._path_of(un_camel_id(name)), 'string', True, False, multi))

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
