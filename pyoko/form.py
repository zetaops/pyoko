# -*-  coding: utf-8 -*-
"""
this module holds classes that responsible for form generation both from models or standalone
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from pyoko.lib.utils import un_camel

class ModelForm(object):
    def __init__(self, model, **kwargs):
        self.model = model
        if not kwargs or 'all' in kwargs:
            kwargs = {'base_fields': 1, 'nodes': 1, 'linked_models': 1}
            if 'all' in kwargs:
                kwargs['list_nodes'] = 1
        self.config = kwargs

    def serialize(self):
        while 1:
            if 'base_fields' in self.config:
                for name, field in self.model._fields.items():
                    if name in ['deleted', 'timestamp']: continue
                    yield {'name': name,
                           'type': field.solr_type,
                           'value': self.model._field_values.get(name, ''),
                           'required': field.required,
                           'title': field.title,
                           'default': field.default() if callable(field.default) else field.default,
                           'section': 'main',
                           'storage': 'main',
                           }
            if 'nodes' in self.config or 'list_nodes' in self.config:
                for node_name, node in self.model._nodes.items():
                    node_type = getattr(self.model, node_name).__class__.__base__.__name__
                    if (node_type == 'Node' and 'nodes' in self.config) or (
                        node_type == 'ListNode' and 'list_nodes' in self.config):
                        instance_node = getattr(self.model, node_name)
                        for name, field in instance_node._fields.items():
                            if name in ['deleted', 'timestamp']: continue
                            yield {'name': "%s.%s" % (un_camel(node_name), name),
                                   'type': field.solr_type,
                                   'title': field.title,
                                   'value': self.model._field_values.get(name, ''),
                                   'required': field.required,
                                   'default': field.default() if callable(field.default) else field.default,
                                   'section': node_name,
                                   'storage': node_type,
                                   }
            if 'linked_models' in self.config:
                for model_attr_name, model in self.model._linked_models.items():
                    yield {'name': "%s_id" % model_attr_name,
                           'model_name': model.__name__,
                           'type': 'model',
                           'title': self.model.title,
                           'value': getattr(self.model, model_attr_name).key,
                           'required': None,
                           'default': None,
                           'section': 'main',
                           }
            break


