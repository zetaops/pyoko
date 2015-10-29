# -*-  coding: utf-8 -*-
"""
this module holds methods that responsible for form generation
both from models or standalone forms
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import six
from pyoko.fields import BaseField
from pyoko.lib.utils import un_camel, to_camel


class ModelForm(object):
    # FIXME: Permission checks
    class Meta:
        title = None
        customize_types = {}
        help_text = ''

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
        # FIXME: Permission checks
        self.model = model or self
        if not kwargs or 'all' in kwargs:
            kwargs.update({'fields': True, 'nodes': True, 'models': True})
            if 'all' in kwargs:
                kwargs['list_nodes'] = True
        if 'nodes' not in kwargs or 'models' not in kwargs or 'fields' not in kwargs:
            kwargs['fields'] = True
        self.config = kwargs
        self.customize_types = kwargs.get('types', getattr(self.Meta, 'customize_types', {}))
        if not hasattr(self.Meta, 'title'):
            self.Meta.title = kwargs.get('title',
                                         getattr(self.model.Meta, 'verbose_name',
                                                 self.model.__class__.__name__))

    def deserialize(self, data):
        """
        returns the model loaded with received form data.

        :param dict data: received form data from client
        """
        # TODO: investigate and integrate necessary security precautions on received data
        # TODO: Add listnode support
        new_instance = self.model.__class__(self.model.context)
        new_instance.key = self.model.key
        for key, val in data.items():
            if key.endswith('_id'):  # linked model
                name = key[:-3]
                linked_model = self.model._linked_models[name][0](self.model.context).objects.get(
                    val)
                setattr(new_instance, name, linked_model)
            elif isinstance(val, six.string_types):  # field
                setattr(new_instance, key, val)
            elif isinstance(val, dict):  # Node
                node = getattr(new_instance, key)
                for k in val:
                    setattr(node, k, val[k])
            elif isinstance(val, list):  # ListNode
                list_node = getattr(new_instance, key)
                for ln_item_data in val:
                    kwargs = {}
                    for k in ln_item_data:
                        if k.endswith('_id'):  # linked model in a ListNode
                            name = k[:-3]
                            kwargs[name] = getattr(list_node, name).__class__(
                                self.model.context).objects.get(ln_item_data[k])
                        else:
                            kwargs[k] = ln_item_data[k]
                    list_node(**kwargs)
        return new_instance

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
            node_data = None
            if (instance_node._is_auto_created or
                    (node_type == 'Node' and 'nodes' not in self.config) or
                    (node_type == 'ListNode' and 'list_nodes' not in self.config)):
                continue
            if node_type == 'Node':
                schema = self.node_schema(instance_node, node_name)
                if self.model.is_in_db():
                    node_data = self.node_data([instance_node], node_name)
            else:  # ListNode
                # to get schema of empty listnode we need to create an instance of it
                if len(instance_node) == 0:
                    instance_node()
                else:
                    node_data = self.node_data(instance_node, node_name)
                schema = self.node_schema(instance_node[0], node_name)
            result.append({'name': node_name,
                           'type': node_type,
                           'title': instance_node.Meta.verbose_name,
                           'schema': schema,
                           'value': node_data if not node_data or node_type == 'ListNode'
                           else node_data[0],
                           'required': None,
                           'default': None,
                           })

    def get_models(self, result):
        for model_attr_name, (model, one_to_one) in self.model._linked_models.items():
            model_instance = getattr(self.model, model_attr_name)
            result.append({'name': "%s_id" % model_attr_name,
                           'model_name': model.__name__,
                           'type': 'model',
                           'title': model.Meta.verbose_name,
                           'value': model_instance.key,
                           'content': (list(self.__class__(model_instance,
                                                           fields=True)._serialize())
                                       if self.model.is_in_db() else None),
                           'required': None,
                           'default': None,
                           })

    def get_fields(self, result):
        for name, field in self.model._fields.items():
            if name in ['deleted', 'timestamp']:
                continue
            result.append({'name': name,
                           'type': self.customize_types.get(name,
                                                            field.solr_type),
                           'value': self.model._field_values.get(name, ''),
                           'required': field.required,
                           'title': field.title,
                           'default': field.default() if callable(
                               field.default) else field.default,
                           })

    def node_schema(self, node, parent_name):
        result = []

        # node_data = {'models': [], 'fields': []}
        for model_attr_name in node._linked_models:
            model_instance = getattr(node, model_attr_name)
            result.append({'name': "%s_id" % model_attr_name,
                           'model_name': model_instance.__class__.__name__,
                           'type': 'model',
                           'title': model_instance.Meta.verbose_name,
                           'required': None, })
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

    def node_data(self, nodes, parent_name):
        # FIXME: Permission checks
        results = []
        for real_node in nodes:
            result = {}
            # node_data = {'models': [], 'fields': []}
            for model_attr_name in real_node._linked_models:
                model_instance = getattr(real_node, model_attr_name)
                result["%s_id" % model_attr_name] = {'key': model_instance.key,
                                                     'verbose_name': model_instance}
            for name, field in real_node._fields.items():
                result[name] = real_node._field_values.get(name, '')
            results.append(result)
        return results


class Form(ModelForm):
    """
    A base class for a custom form with pyoko.fields.
    Has some fake dicts to simulate model object
    """

    def __init__(self, *args, **kwargs):
        self._nodes = {}
        self._fields = {}
        self._linked_models = {}
        self._field_values = {}
        self.context = None
        self.key = None
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
