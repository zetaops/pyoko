# -*-  coding: utf-8 -*-
"""
this module holds methods that responsible for form generation
both from models or standalone forms
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import os

from collections import defaultdict

from pyoko.lib.utils import un_camel_id

from .fields import *
import six

BYPASS_REQUIRED_FIELDS = os.getenv('BYPASS_REQUIRED_FIELDS')


class FormMeta(type):
    _meta = None

    def __new__(mcs, name, bases, attrs):
        if name == 'ModelForm':
            FormMeta._meta = attrs['Meta']
        else:
            if 'Meta' not in attrs:
                attrs['Meta'] = type('Meta', (object,), dict(FormMeta._meta.__dict__))
            else:
                for k, v in FormMeta._meta.__dict__.items():
                    if k not in attrs['Meta'].__dict__:
                        setattr(attrs['Meta'], k, v)
        new_class = super(FormMeta, mcs).__new__(mcs, name, bases, attrs)
        return new_class


@six.add_metaclass(FormMeta)
class ModelForm(object):
    class Meta:
        """
        attribute customisation:
        attributes = {
           # field_name    attrib_name   value(s)
            'kadro_id': [('filters', {'durum': 1}), ]
        }
        """
        customize_types = {}
        help_text = None
        title = None
        include = []
        exclude = []
        # attributes = defaultdict(list)

    def __init__(self, model=None, exclude=None, include=None, types=None, title=None, **kwargs):
        """
        A serializer / deserializer for models and custom
        forms that built with pyoko.fields

        .. note:: *include* and *exclude* does not support fields that placed in nodes.

        :param pyoko.Model model: A pyoko model instance, may be empty
        :param list exclude: list of fields to be excluded from serialization
        :param list include: list of fields to be included into serialization
        :param dict types: override type of fields
        """
        self._model = model or self
        self._config = {'fields': True, 'nodes': True, 'models': True, 'list_nodes': True}
        self._config.update(kwargs)
        self.readable = False
        self._ordered_fields = []
        self.exclude = exclude or self.Meta.exclude
        self.include = include or self.Meta.include
        self.non_data_fields = ['object_key']
        self.customize_types = types or getattr(self.Meta, 'customize_types', {})
        self.help_text = self.Meta.help_text or getattr(self._model.Meta, 'help_text', None)
        self.title = title or self.Meta.title or getattr(self._model.Meta, 'verbose_name',
                                                         self._model.__class__.__name__)

    def deserialize(self, data):
        """
        returns the model loaded with received form data.

        :param dict data: received form data from client
        """
        # FIXME: investigate and integrate necessary security precautions on received data
        # ie: received keys should  be defined in the form
        # compare with output of self._serialize()
        self.prepare_fields()
        new_instance = self._model
        new_instance.key = self._model.key
        for key, val in data.items():
            if key in self.non_data_fields:
                continue
            if key.endswith('_id') and val:  # linked model
                name = key[:-3]
                linked_model = self._model._linked_models[name][0](
                    self._model.context).objects.get(
                        val)
                setattr(new_instance, name, linked_model)
            elif isinstance(val, (six.string_types, bool, int, float)):  # field
                setattr(new_instance, key, val)
            elif isinstance(val, dict):  # Node
                node = getattr(new_instance, key)
                for k in val:
                    setattr(node, k, val[k])
            elif isinstance(val, list):  # ListNode
                # get the listnode instance from model
                list_node = getattr(new_instance, key)
                # clear out it's existing content
                list_node.clear()
                # fill with form input
                for ln_item_data in val:
                    kwargs = {}
                    for k in ln_item_data:
                        if k.endswith('_id'):  # linked model in a ListNode
                            name = k[:-3]
                            kwargs[name] = getattr(list_node, name).__class__(
                                    self._model.context).objects.get(ln_item_data[k])
                        else:
                            kwargs[k] = ln_item_data[k]
                    list_node(**kwargs)
        return new_instance

    def _serialize(self, readable=False):
        """
        returns serialized version of all parts of the model or form

        :type readable: create human readable output
            ie: use get_field_name_display()
        :return: list of serialized model fields
        :rtype: list
        """
        self.prepare_fields()
        self.readable = readable
        result = []
        if self._config['fields']:
            self._get_fields(result, self._model)
        if self is not self._model:  # to allow additional fields
            try:
                self._get_fields(result, self)
            except AttributeError:
                # TODO: all "forms" of world, unite!
                pass
        if self._config['models']:
            self._get_models(result)
        if self._config['nodes'] or self._config['list_nodes']:
            self._get_nodes(result)

        return result

    def _filter_out(self, name):
        """
        returns true if given name should be
        filtered out from serialization.

        :param name: field, node or model name.
        :return:
        """
        if self.exclude and name in self.exclude:
            return True
        if self.include and name not in self.include:
            return True

    def _get_nodes(self, result):
        for node_name in self._model._nodes:
            if self._filter_out(node_name):
                continue
            instance_node = getattr(self._model, node_name)
            node_type = instance_node.__class__.__base__.__name__
            node_data = None
            if (instance_node._is_auto_created or
                    (node_type == 'Node' and self._config['nodes'] is None) or
                    (node_type == 'ListNode' and self._config['list_nodes'] is None)):
                continue
            if node_type == 'Node':
                schema = self._node_schema(instance_node, node_name)
                if self._model.is_in_db():
                    node_data = self._node_data([instance_node], node_name)
            else:  # ListNode
                # to get schema of empty listnode we need to create an instance of it
                if len(instance_node) == 0:
                    instance_node()
                else:
                    node_data = self._node_data(instance_node, node_name)
                schema = self._node_schema(instance_node[0], node_name)
            result.append({'name': node_name,
                           'type': node_type,
                           'title': instance_node.Meta.verbose_name,
                           'schema': schema,
                           'value': node_data if not node_data or node_type == 'ListNode'
                           else node_data[0],
                           'required': None,
                           'default': None,
                           })

    def _get_models(self, result):
        for mdl_name, links in self._model._linked_models.items():
            for lnk in links:
                field_name = lnk.get('field', mdl_name)
                if self._filter_out(field_name):
                    continue
                model = lnk['mdl']
                model_instance = getattr(self._model, field_name)
                result.append({'name': un_camel_id(field_name),
                               'model_name': model.__name__,
                               'type': 'model',
                               'title': model.Meta.verbose_name,
                               'value': model_instance.key,
                               'content': (self.__class__(model_instance,
                                                          models=False,
                                                          list_nodes=False,
                                                          nodes=False)._serialize()
                                           if self._model.is_in_db() else None),
                               'required': None,
                               'default': None,
                               })

    def _serialize_value(self, val):
        if isinstance(val, datetime.datetime):
            return val.strftime(DATE_TIME_FORMAT)
        elif isinstance(val, datetime.date):
            return val.strftime(DATE_FORMAT)
        elif isinstance(val, BaseField):
            return None
        else:
            return val or ''

    def _get_fields(self, result, model_obj):
        for name, field in model_obj._ordered_fields:
            if not isinstance(field, Button) and (
                    name in ['deleted', 'timestamp'] or self._filter_out(name)):
                continue
            if self.readable:
                val = model_obj.get_humane_value(name)
            else:
                val = self._serialize_value(getattr(model_obj, name))
            result.append({'name': name,
                           'type': self.customize_types.get(name,
                                                            field.solr_type),
                           'value': val,
                           'required': (False if BYPASS_REQUIRED_FIELDS or
                                                 field.solr_type is 'boolean' else field.required),
                           'choices': getattr(field, 'choices', None),
                           'kwargs': field.kwargs,
                           'title': field.title,
                           'default': field.default() if callable(
                               field.default) else field.default,
                           })

    def _node_schema(self, node, parent_name):
        result = []

        # node_data = {'models': [], 'fields': []}
        for model_attr_name in node._linked_models:
            model_instance = getattr(node, model_attr_name)
            result.append({'name': "%s_id" % model_attr_name,
                           'model_name': model_instance.__class__.__name__,
                           'type': 'model',
                           'title': model_instance.Meta.verbose_name,
                           'required': None,})
        for name, field in node._fields.items():
            result.append({
                'name': name,
                'type': self.customize_types.get(name, field.solr_type),
                'title': field.title,
                'required': field.required,
                'default': field.default() if callable(field.default)
                else field.default,
            })
        return result

    def prepare_fields(self):
        pass

    def _node_data(self, nodes, parent_name):
        results = []
        for real_node in nodes:
            result = {}
            # node_data = {'models': [], 'fields': []}
            for model_attr_name in real_node._linked_models:
                model_instance = getattr(real_node, model_attr_name)
                result["%s_id" % model_attr_name] = {'key': model_instance.key,
                                                     'verbose_name': model_instance.Meta.verbose_name,
                                                     'unicode': six.text_type(model_instance)
                                                     }
            for name, field in real_node._fields.items():
                result[name] = self._serialize_value(real_node._field_values.get(name))
            results.append(result)
        return results


class Form(ModelForm):
    """
    A base class for a custom form with pyoko.fields.
    Has some fake properties to simulate model object
    """

    def __init__(self, *args, **kwargs):
        self.context = kwargs.get('current')
        self._nodes = {}
        self._fields = {}
        self._linked_models = {}
        self._field_values = {}
        self.key = None
        self._data = {}
        self._ordered_fields = []
        super(Form, self).__init__(*args, **kwargs)

    def prepare_fields(self):
        _items = list(self.__class__.__dict__.items()) + list(self.__dict__.items())
        for key, val in _items:
            if isinstance(val, BaseField):
                val.name = key
                self._fields[key] = val
            if isinstance(val, (Button,)):
                self.non_data_fields.append(key)
        for v in sorted(self._fields.items(), key=lambda x: x[1]._order):
            self._ordered_fields.append((v[0], v[1]))

    def get_humane_value(self, name):
        return name

    def is_in_db(self):
        return False

    def set_data(self, data):
        """
        fills form with data
        :param dict data:
        :return: self
        """
        for name in self._fields:
            setattr(self, name, data.get(name))
        return self


class Button(BaseField):
    def __init__(self, *args, **kwargs):
        # self.cmd = kwargs.pop('cmd', None)
        # self.position = kwargs.pop('position', 'bottom')
        # self.validation = kwargs.pop('validation', True)
        # self.flow = kwargs.pop('flow', None)
        self.kwargs = kwargs
        super(Button, self).__init__(*args, **kwargs)

    solr_type = 'button'
