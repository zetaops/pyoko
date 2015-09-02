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
        # TODO: to return in consistent order we should iterate on a sorted list (by keys)
        while 1:
            if 'fields' in self.config:
                for name, field in self.model._fields.items():
                    if name in ['deleted', 'timestamp']: continue
                    value = self.model._field_values.get(name, '')
                    if value:
                        default = None
                    else:
                        default = field.default() if callable(
                            field.default) else field.default
                    yield {'name': name,
                           'type': self.customize_types.get(name,
                                                            field.solr_type),
                           'value': value,
                           'required': field.required,
                           'title': field.title,
                           'default': default,
                           'section': 'main',
                           'storage': 'main',
                           }
            if 'nodes' in self.config or 'list_nodes' in self.config:
                for node_name in self.model._nodes:
                    instance_node = getattr(self.model, node_name)
                    if instance_node._is_auto_created:
                        continue
                    node_type = instance_node.__class__.__base__.__name__
                    if (node_type == 'Node' and 'nodes' in self.config) or (
                            node_type == 'ListNode' and 'list_nodes' in self.config):
                        if node_type == 'Node':
                            nodes = [instance_node]
                        else:
                            nodes = instance_node
                        for real_node in nodes:
                            for model_attr_name, (model, one_to_one) in \
                                    real_node._linked_models.items():
                                model_instance = getattr(real_node, model_attr_name)
                                yield {'name': "%s_id" % model_attr_name,
                                       'model_name': model.__name__,
                                       'type': 'model',
                                       'title': model.__name__,
                                       'value': model_instance.key,
                                       'content': list(self.__class__(model_instance, fields=True,
                                                                      models=True)._serialize()),
                                       'required': None,
                                       'default': None,
                                       'section': 'main',
                                       }
                            for name, field in real_node._fields.items():
                                if name in ['deleted', 'timestamp']:
                                    continue
                                yield {
                                    'name': "%s.%s" % (un_camel(node_name), name),
                                    'type': self.customize_types.get(name, field.solr_type),
                                    'title': field.title,
                                    'value': real_node._field_values.get(name, ''),
                                    'required': field.required,
                                    'default': field.default() if callable(field.default)
                                    else field.default,
                                    'section': node_name,
                                    'storage': node_type,
                                }
            if 'models' in self.config:
                for model_attr_name, (model, one_to_one) in self.model._linked_models.items():
                    model_instance = getattr(self.model, model_attr_name)
                    yield {'name': "%s_id" % model_attr_name,
                           'model_name': model.__name__,
                           'type': 'model',
                           'title': model.__name__,
                           'value': model_instance.key,
                           'content': list(self.__class__(model_instance,
                                                          fields=True)._serialize()),
                           'required': None,
                           'default': None,
                           'section': 'main',
                           }
            break


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
