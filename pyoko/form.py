# -*-  coding: utf-8 -*-
"""
this module holds classes that responsible for form generation both from models or standalone
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from pyoko.field import BaseField
from pyoko.lib.utils import un_camel, to_camel


class ModelForm(object):
    TYPE_OVERRIDES = {}

    def __init__(self, model=None, **kwargs):
        """
        keyword arguments:
            fields = True
            nodes = True
            linked_models = True
            list_nodes = False
            types = {'field_name':'type', 'password':'password'} modify type of fields.
        :param pyoko.Model model: A pyoko model instance, may be empty or full.
        :param dict kwargs: configuration options
        """
        self.model = model or self
        if not kwargs or 'all' in kwargs:
            kwargs.update({'fields': True, 'nodes': True, 'models': True})
            if 'all' in kwargs:
                kwargs['list_nodes'] = True
        if 'nodes' not in kwargs or 'models' not in kwargs or 'fields' not in kwargs:
            kwargs['fields'] = True
        self.config = kwargs
        self.customize_types = kwargs.get('types', self.TYPE_OVERRIDES)
        self.title = kwargs.get('title', self.model.__class__.__name__)
        print("FORM_SERIALIZER_CONF %s" % self.config)

    def deserialize(self, data):
        """
        returns the model loaded with received form data.

        :param dict data: received form data from client
        """
        # FIXME: we should investigate and integrate necessary security precautions on received data
        # TODO: add listnode support when format of incoming data for listnodes defined
        proccessed_data = {}
        for key, val in data.items():
            if '.' in key:
                keys = key.split('.')
                if keys[0] not in proccessed_data:
                    proccessed_data[keys[0]] = {}
                proccessed_data[keys[0]][keys[1]] = val
            else:
                proccessed_data[key] = val
        self.model.set_data(proccessed_data)
        return self.model

    def _serialize(self):
        """
        :return: list of serialized model fields
        :rtype: list
        """
        result = []
        if 'fields' in self.config:
            self.get_fields(result)
        if 'models' in self.config:
            self.get_models(result)
        if 'nodes' in self.config or 'list_nodes' in self.config:
            self.get_nodes(result)
        return result

    def get_nodes(self, result):
        for node_name in self.model._nodes:
            instance_node = getattr(self.model, node_name)
            node_type = instance_node.__class__.__base__.__name__
            if (instance_node._is_auto_created or
                    (node_type == 'Node' and 'nodes' not in self.config) or
                    (node_type == 'ListNode' and 'list_nodes' not in self.config)):
                continue
            if node_type == 'Node':
                nodes = [instance_node]
            else:
                nodes = instance_node
            result.append({'name': node_name,
                           'type': node_type,
                           'title': node_name,
                           'value': "!",
                           'required': None,
                           'default': None,
                           # 'section': 'main',
                           'models': self.serialize_node_models(nodes, node_name),
                           'fields': self.serialize_node_fields(nodes, node_name),
                           })

    def get_models(self, result):
        for model_attr_name, (model, one_to_one) in self.model._linked_models.items():
            model_instance = getattr(self.model, model_attr_name)
            result.append({'name': "%s_id" % model_attr_name,
                           'model_name': model.__name__,
                           'type': 'model',
                           'title': model.__name__,
                           'value': model_instance.key,
                           'content': list(self.__class__(model_instance,
                                                          fields=True)._serialize()),
                           'required': None,
                           'default': None,
                           # 'section': 'main',
                           })

    def get_fields(self, result):
        for name, field in self.model._fields.items():
            if name in ['deleted', 'timestamp']: continue
            value = self.model._field_values.get(name, '')
            if value:
                default = None
            else:
                default = field.default() if callable(
                    field.default) else field.default
            result.append({'name': name,
                           'type': self.customize_types.get(name,
                                                            field.solr_type),
                           'value': value,
                           'required': field.required,
                           'title': field.title,
                           'default': default,
                           # 'section': 'main',
                           # 'storage': 'main',
                           })

    def serialize_node_models(self, nodes, parent_name):
        result = []
        for real_node in nodes:
            for model_attr_name in real_node._linked_models:
                model_instance = getattr(real_node, model_attr_name)
                result.append({'name': "%s_id" % model_attr_name,
                               'model_name': model_instance.__class__.__name__,
                               'type': 'model',
                               'title': model_instance.__class__.__name__,
                               'value': model_instance.key,
                               'content': list(self.__class__(model_instance, fields=True,
                                                              models=True)._serialize()),
                               'required': None,
                               'default': None,
                               # 'section': parent_name,
                               })
        return result

    def serialize_node_fields(self, nodes, parent_name):
        result = []
        for real_node in nodes:
            for name, field in real_node._fields.items():
                result.append({
                    'name': "%s.%s" % (un_camel(parent_name), name),
                    'type': self.customize_types.get(name, field.solr_type),
                    'title': field.title,
                    'value': real_node._field_values.get(name, ''),
                    'required': field.required,
                    'default': field.default() if callable(field.default)
                    else field.default,
                    # 'section': parent_name,
                })
        return result


class Form(ModelForm):
    """
    base class for a custom form with pyoko.fields
    """

    def __init__(self, *args, **kwargs):
        self._nodes = {}
        self._fields = {}
        self._linked_models = {}
        self._field_values = {}
        for key, val in self.__class__.__dict__.items():
            if isinstance(val, BaseField):
                val.name = key
                self._fields[key] = val
        super(Form, self).__init__(*args, **kwargs)

    def set_data(self, data):
        """
        fills form with data
        :param dict data:
        :return: self
        """
        for name in self._fields:
            setattr(self, name, data.get(name))
        return self