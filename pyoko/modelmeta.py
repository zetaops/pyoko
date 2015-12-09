# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from collections import defaultdict

from pyoko.conf import settings
from pyoko.db.base import DBObjects
from pyoko.lib.utils import un_camel
from pyoko.registry import Registry
from . import fields as field

model_registry = Registry()


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
    def process_attributes(attrs, node_name):
        """
        prepare the model fields, nodes and relations

        :param node_name: name of the node we are currently processing
        :param dict attrs: attribute dict
        """
        attrs['_nodes'] = {}
        attrs['_linked_models'] = defaultdict(list)
        attrs['_lazy_linked_models'] = defaultdict(list)
        attrs['_fields'] = {}
        # attrs['_many_to_models'] = []

        # iterating over attributes of the soon to be created class object.
        for key, attr in list(attrs.items()):
            # if it's a class (not instance) and it's type is Node or ListNode
            if hasattr(attr, '__base__') and getattr(attr.__base__, '_TYPE', '') in ['Node',
                                                                                     'ListNode']:
                attrs['_nodes'][key] = attrs.pop(key)
            else:  # otherwise it should be a field or linked model
                attr_type = getattr(attr, '_TYPE', '')

                if attr_type == 'Model':
                    lnk_mdl_ins = attrs.pop(key)
                    attrs['_linked_models'][key].append({
                        'mdl': lnk_mdl_ins.__class__,
                        'o2o': lnk_mdl_ins._is_one_to_one,
                        'reverse': lnk_mdl_ins.reverse_name,
                        'verbose': lnk_mdl_ins.verbose_name,
                        'field': key
                    })
                elif attr_type == 'Field':
                    attr.name = key
                    attrs['_fields'][key] = attr
                elif attr_type == 'Link':
                    lzy_lnk = attrs.pop(key)
                    attrs['_lazy_linked_models'][key].append({'from': node_name,
                                                              'to': lzy_lnk.link_to,
                                                              'o2o': lzy_lnk.one_to_one,
                                                              'verbose': lzy_lnk.verbose_name,
                                                              'reverse': lzy_lnk.reverse_name,
                                                              'field': key})

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
