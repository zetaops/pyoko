# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import difflib

import datetime
from copy import copy

import lazy_object_proxy
import six

from six import add_metaclass
from uuid import uuid4

from collections import defaultdict

from pyoko.exceptions import ObjectDoesNotExist, ValidationError, MultipleObjectsReturned
from .conf import settings
from .lib.utils import get_object_from_path, lazy_property, un_camel, un_camel_id
from .modelmeta import ModelMeta

SOLR_SUPPORTED_TYPES = ['string', 'text_general', 'float', 'int', 'boolean',
                        'date', 'long', 'text_tr']


class LazyModel(lazy_object_proxy.Proxy):
    key = None
    verbose_name = None
    null = False
    _TYPE = 'Model'

    @property
    def exist(self):
        return bool(self.key)

    def get_verbose_name(self):
        return self.verbose_name or self.Meta.verbose_name

    def __init__(self, wrapped, null, verbose_name):
        self.verbose_name = verbose_name
        self.null = null
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

    def setattr(self, key, val):
        object.__setattr__(self, key, val)

    def setattrs(self, **kwargs):
        self.__dict__.update(kwargs)

    @lazy_property
    def _prop_list(self):
        return (list(self.__dict__.keys()) +
                list(self.__class__.__dict__.keys()) +
                list(self._fields.keys()))

    def __setattr__(self, key, val):
        if (key not in self.__dict__ and
                    key not in self.__class__.__dict__ and
                    key not in self._fields):
            matches = list(set(difflib.get_close_matches(key, self._prop_list, 4, 0.5)))
            error_msg = "Unexpected assignment, do you mistyped a field name \"%s\"." % key
            if matches:
                error_msg += '\n\nDid you mean one of these?  ' % '""'.join(matches)
            print(self._prop_list)
            raise AttributeError(error_msg)
        if key not in self._fields:
            _attr = getattr(self, key)
            if _attr is not None and _attr.__class__.__name__ != val.__class__.__name__:
                raise ValidationError(
                    "Assigned object's (%s) type (%s) does not matches to \"%s %s\" " %
                    (key,
                     val.__class__.__name__,
                     _attr.__class__.__name__,
                     getattr(_attr, '_TYPE', None)))
        object.__setattr__(self, key, val)

    def __init__(self, **kwargs):
        self.setattrs(
            _node_path=[],
            _field_values={},
            _secured_data={},
            _choice_fields=[],
            _data={},
            _choices_manager=get_object_from_path(settings.CATALOG_DATA_MANAGER),

        )
        super(Node, self).__init__()
        try:
            self._root_node
        except:
            self.setattrs(
                _root_node=kwargs.pop('_root_node', None),
                _context=kwargs.pop('context', None),
                _model_in_node=defaultdict(list)
            )
        # self._context = kwargs.pop('context', None)
        # self._field_values = {}
        # self._data = {}
        # self._choice_fields = []
        # self._choices_manager = get_object_from_path(settings.CATALOG_DATA_MANAGER)
        # if model has cell_filters that applies to current user,
        # filtered values will be kept in _secured_data dict
        # self._secured_data = {}
        # linked models registry for finding the list_nodes that contains a link to us
        # self._model_in_node = defaultdict(list)
        self._instantiate_linked_models(kwargs)
        self._instantiate_nodes()
        self._set_fields_values(kwargs)

    def get_verbose_name(self):
        """
        Returns:
             value of title attribute or verbose name of class
        """
        try:
            return self.__class__.Meta.title or self.__class__.__name__
        except AttributeError:
            return self.__class__.__name__

    @lazy_property
    def _ordered_fields(self):
        return sorted(self._fields.items(), key=lambda kv: kv[1]._order)

    @classmethod
    def _add_linked_model(cls, mdl, link_source=False, null=False, o2o=False, field=None,
                          reverse=None, verbose=None, is_set=False, m2m=False, reverse_link=False,
                          model_listnode=False, **kwargs):
        lnk = {
            'null': null,
            'link_source': link_source,
            'o2o': o2o,
            'mdl': mdl,
            'field': field,
            'reverse': reverse,
            'verbose': verbose,
            'is_set': is_set,
            'm2m': m2m,
            'reverse_link': reverse_link,
            'model_listnode': model_listnode
        }
        lnksrc = kwargs.pop('lnksrc', '')
        lnk.update(kwargs)
        debug_lnk = lnk.copy()
        debug_lnk['lnksrc'] = lnksrc
        cls._debug_linked_models[mdl.__name__].append(debug_lnk)
        if lnk not in cls._linked_models[mdl.__name__]:
            cls._linked_models[mdl.__name__].append(lnk)

    @classmethod
    def _get_bucket_name(cls):
        return getattr(cls.Meta, 'bucket_name', un_camel(cls.__name__))

    def _path_of(self, prop):
        """
        returns the dotted path of the given model attribute
        """
        root_name = (self._root_node or self)._get_bucket_name()
        return ('.'.join(list(self._node_path + [un_camel(self.__class__.__name__),
                                                 prop]))).replace('%s.' % root_name, '')

    @classmethod
    def get_field(cls, field_name):
        return cls._fields.get(field_name)

    @classmethod
    def get_link(cls, **kw):
        """
        Get first item of get_links() method
        """
        models = cls.get_links(**kw)
        return models[0]

    @classmethod
    def get_links(cls, **kw):
        """
        Linked models from this model

        Keyword Args:
            filter by items of _linked_models

            startswith: Bool, use startswith for filtering instead of exact matching.
                Only works for filtering over one field.

        Returns:
            Link list
        """
        # TODO: Add tests for this method
        startswith = kw.pop('startswith', False)
        kwitems = list(kw.items())  # Dictionary items is not indexible in Python 3
        constraint = set(kwitems)
        models = []
        for links in cls._linked_models.values():
            for lnk in links:
                if not constraint or constraint.issubset(set(lnk.items())):
                    models.append(lnk)
                elif startswith and lnk[kwitems[0][0]].startswith(kwitems[0][1]):
                    models.append(lnk)
        return models

    def _instantiate_linked_models(self, data=None):

        from .model import Model
        def foo_model(modl, context, null, verbose_name):
            return LazyModel(lambda: modl(context), null, verbose_name)

        for lnk in self.get_links(is_set=False):
            # if lnk['is_set']:
            #     continue
            self.setattr(lnk['field'] + '_id', "")
            if data:
                # data can be came from db or user
                if lnk['field'] in data and isinstance(data[lnk['field']], Model):
                    # this should be coming from user,
                    # and it should be a model instance
                    linked_mdl_ins = data[lnk['field']]
                    self.setattr(lnk['field'], linked_mdl_ins)
                    try:
                        if lnk['o2o'] or lnk['reverse_link']:
                            kw = {'mdl': lnk['mdl'], 'link_source': not lnk['link_source']}
                            if self._TYPE == 'ListNode' and len(self._root_node.get_links(**kw))>1:
                                kw['field'] = "%s.%s" % (self.__class__.__name__, lnk['field'])
                            self._root_node._add_back_link(linked_mdl_ins,
                                                           self._root_node.get_link(**kw))

                    except:
                        pass
                else:
                    _name = un_camel_id(lnk['field'])
                    if _name in data and data[_name] is not None:
                        # this is coming from db,
                        # we're preparing a lazy model loader
                        def fo(modl, context, key):
                            def fo2():
                                try:  # workaround for #5094 / GH-46
                                    return modl(context,
                                                null=lnk['null'],
                                                verbose_name=lnk['verbose']).objects.get(key)
                                except (ObjectDoesNotExist, MultipleObjectsReturned):
                                    missing_object = modl(context,
                                                          null=lnk['null'],
                                                          verbose_name=lnk['verbose'])
                                    missing_object._exists = False
                                    return missing_object

                            return fo2

                        obj = LazyModel(fo(lnk['mdl'], self._context, data[_name]),
                                        lnk['null'],
                                        lnk['verbose'])
                        obj.key = data[_name]
                        obj.null = lnk['null']
                        self.setattr(lnk['field'], obj)
                    else:
                        # creating a lazy proxy for empty linked model
                        # Note: this should be explicitly saved before _root_node model!
                        self.setattr(lnk['field'],
                                     foo_model(lnk['mdl'],
                                               self._context,
                                               lnk['null'],
                                               lnk['verbose']))
            else:
                # creating an lazy proxy for empty linked model
                # Note: this should be explicitly saved before _root_node model!
                self.setattr(lnk['field'], foo_model(lnk['mdl'],
                                                     self._context,
                                                     lnk['null'],
                                                     lnk['verbose']))
                # setattr(self, lnk['field'], LazyModel(lambda: lnk['mdl'](self._context)))

    def _instantiate_node(self, name, klass):
        # instantiate given node, pass path and _root_node info
        ins = klass(**{'context': self._context,
                       '_root_node': self._root_node or self})
        ins.setattr('_node_path', self._node_path + [un_camel(self.__class__.__name__)])
        self.setattr(name, ins)
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
        """
        Returns a human readble/meaningful value for the field

        Args:
            name (str): Model field name

        Returns:
            Human readble field value
        """
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
        Fill the fields of this node

        Args:
            kwargs: Field values
        """
        # if kwargs:
        for name, _field in self._fields.items():
            val = None
            if name in kwargs:
                val = kwargs.get(name, self._field_values.get(name))
                path_name = self._path_of(name)
                _root_node = self._root_node or self
                if path_name in _root_node.get_unpermitted_fields():
                    self._secured_data[path_name] = val
                    continue
            elif _field.default:
                val = _field.default() if callable(_field.default) else _field.default
            if val is not None:
                if not kwargs.get('from_db'):
                    self.setattr(name, val)
                else:
                    _field._load_data(self, val)

            # if not self._field_values.get(name):
            #     self._field_values[name] = getattr(self, name)
            if _field.choices is not None:
                self._choice_fields.append(name)
                self._set_get_choice_display_method(name, _field, val)

    def _set_get_choice_display_method(self, name, _field, val):
        # adding get_%s_display() methods for fields which has "choices" attribute
        def get_choice_display_closure():
            choices, value = copy(_field.choices), copy(val)
            return lambda: self._choices_manager(choices, value)

        self.setattr('get_%s_display' % name, get_choice_display_closure())

    def _collect_index_fields(self, in_multi=False):
        """
        Collects fields which will be indexed.

        Args:
            in_multi (bool): if we are in a ListNode or not

        Returns:
            [(field_name, solr_type, is_indexed, is_stored, is_multi]
        """
        result = []
        # if not model_name:
        #     model_name = self._get_bucket_name()
        from .listnode import ListNode
        multi = in_multi or isinstance(self, ListNode)
        for lnk in self.get_links(is_set=False):
            result.append(
                (self._path_of(un_camel_id(lnk['field'])), 'string', True, settings.DEBUG, multi))

        for name, field_ins in self._fields.items():
            field_name = self._path_of(name)
            solr_type = (field_ins.solr_type
                         if field_ins.solr_type in SOLR_SUPPORTED_TYPES else 'ignored')
            result.append((field_name,
                           solr_type,
                           field_ins.index,
                           field_ins.store or settings.DEBUG,
                           multi))
        for mdl_ins in self._nodes:
            result.extend(getattr(self, mdl_ins)._collect_index_fields(multi))
        return result

    def _load_data(self, data, from_db=False):
        """
        With the data returned from riak:
        - fills model's fields, nodes and listnodes
        - instantiates linked model instances

        Args:
            from_db (bool): if data coming from db instead of calling
                self._set_fields_values() we simply use field's _load_data method.
        """
        self._data = data.copy()
        self._data['from_db'] = from_db
        self._fill_nodes(self._data)
        self._set_fields_values(self._data)
        self._instantiate_linked_models(self._data)
        del self._data['from_db']
        return self

    def _clean_node_value(self, dct):
        # get values of nodes
        for name in self._nodes:
            node = getattr(self, name)
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
        # get keys of linked models
        for lnk in self.get_links(is_set=False):
            lnkd_mdl = getattr(self, lnk['field'])
            mdl_id = un_camel_id(lnk['field'])
            dct[mdl_id] = getattr(self, mdl_id) or (lnkd_mdl.key if lnkd_mdl is not None else '')

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
