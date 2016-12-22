# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import pprint
from collections import defaultdict

from pyoko.lib.utils import un_camel


class FakeContext(object):
    def has_permission(self, perm):
        return True


super_fake_context = FakeContext()


class Registry(object):
    def __init__(self):
        self.registry = {}
        self.lazy_models = defaultdict(list)
        self.app_registry = defaultdict(dict)

    def register_model(self, mdl):
        if mdl.__name__ not in self.registry and mdl.__name__ != 'FakeModel':
            self.registry[mdl.__name__] = mdl
            self.app_registry[mdl.Meta.app][mdl.__name__] = mdl
            self._process_links_from_nodes_of_mdl(mdl)
            self._process_links(mdl)
            self._pre_process_lazy_links(mdl)

    def _process_links(self, mdl):
        for lnk in mdl.get_links(m2m=False):
            # custom reverse name or model name if one to one
            # or model_name_set otherwise
            reverse_name = un_camel(lnk['reverse'] or mdl.__name__ + ('' if lnk['o2o'] else "_%s_set" % lnk['field']))
            if lnk['reverse'] is None:
                # fill the missing 'reverse' info
                idx = mdl._linked_models[lnk['mdl'].__name__].index(lnk)
                lnk['reverse'] = reverse_name
                mdl._linked_models[lnk['mdl'].__name__][idx] = lnk
            # self.link_registry[lnk['mdl']].append((name, mdl, reverse_name))
            if lnk['o2o']:
                self._create_one_to_one(mdl,
                                        lnk['mdl'],
                                        reverse_name)
                lnk['mdl']._add_linked_model(mdl,
                                             o2o=True,
                                             field=reverse_name,
                                             null=lnk['null'],
                                             reverse=lnk['field'],
                                             reverse_link=lnk['reverse_link'],
                                             lnksrc='_process_links__o2o')
            else:
                lnk['mdl']._add_linked_model(mdl,
                                             reverse=lnk['field'],
                                             null=lnk['null'],
                                             m2m='.' in lnk['field'],
                                             field=reverse_name, is_set=True,
                                             reverse_link=lnk['reverse_link'],
                                             lnksrc='_process_links__O2M')
                if lnk['reverse_link']:
                    self._create_one_to_many(mdl, lnk['mdl'], reverse_name)

    def _pre_process_lazy_links(self, mdl):
        for links in mdl._lazy_linked_models.values():
            for lzy_lnk in links:
                self.lazy_models[lzy_lnk['to']].append(lzy_lnk)
                if lzy_lnk['to'] in self.registry:
                    self._process_lazy_links(self.registry[lzy_lnk['to']])
        self._process_lazy_links(mdl)

    def _process_lazy_links(self, mdl):
        if mdl.__name__ in self.lazy_models:
            for lm in self.lazy_models[mdl.__name__]:
                target_mdl = self.registry[lm['from']]
                reverse_name = un_camel(
                    lm['reverse'] or lm['from'] + ('' if lm['o2o'] else "_%s_set" % lm['field']))
                target_mdl._add_linked_model(mdl,
                                             reverse=reverse_name,
                                             field=lm['field'],
                                             verbose=lm['verbose'],
                                             link_source=False,
                                             reverse_link=lm['reverse_link'],
                                             lnksrc='prcs_lzy_lnks_from_target')
                mdl._add_linked_model(target_mdl,
                                      link_source=True,
                                      reverse=lm['field'],
                                      field=reverse_name,
                                      is_set=True,
                                      reverse_link=lm['reverse_link'],
                                      lnksrc='prcs_lzy_lnks_from_mdl')

                setattr(target_mdl, lm['field'], mdl)
                if lm['reverse_link']:
                    self._create_one_to_many(target_mdl, mdl, reverse_name)

    def _process_links_from_nodes_of_mdl(self, source_mdl):
        _src_mdl_ins = source_mdl(super_fake_context)
        for node_name in source_mdl._nodes.keys():
            node = getattr(_src_mdl_ins, node_name)
            for lnk in node.get_links():
                reverse_name = lnk['reverse'] or un_camel(source_mdl.__name__ + node_name) + (
                '' if lnk['o2o'] else "_%s_set" % lnk['field'])
                if lnk['o2o']:
                    lnk['mdl']._add_linked_model(source_mdl,
                                                 o2o=True,
                                                 field=reverse_name,
                                                 reverse=lnk['field'],
                                                 null=lnk['null'],
                                                 lnksrc='_prcs_lnks_frm_nodes_of_mdl__o2o')
                    self._create_one_to_one(source_mdl,
                                            target_mdl=lnk['mdl'],
                                            field_name=reverse_name)
                else:
                    lnk['mdl']._add_linked_model(source_mdl,
                                                 o2o=False,
                                                 null=lnk['null'],
                                                 field=reverse_name,
                                                 reverse=node_name + '.' + lnk['field'],
                                                 m2m=node._TYPE == 'ListNode',
                                                 is_set=True,
                                                 reverse_link=lnk['reverse_link'],
                                                 lnksrc='_prcs_lnks_frm_nodes_of_mdl__O2M')

                    source_mdl._add_linked_model(lnk['mdl'],
                                                 o2o=False,
                                                 null=lnk['null'],
                                                 field=node_name + '.' + lnk['field'],
                                                 reverse=reverse_name,
                                                 m2m=node._TYPE == 'ListNode',
                                                 is_set=True,
                                                 reverse_link=lnk['reverse_link'],
                                                 model_listnode=True,
                                                 lnksrc='_prcs_lnks_frm_nodes_of_mdl__O2M_SRCMDL')
                    if lnk['reverse_link']:
                        self._create_one_to_many(source_mdl,
                                                 target_mdl=lnk['mdl'],
                                                 listnode_name=reverse_name)

    def _create_one_to_one(self, source_mdl, target_mdl, field_name):
        mdl_instance = source_mdl(one_to_one=True)
        mdl_instance.setattrs(_is_auto_created=True)
        for instance_ref in target_mdl._instance_registry:
            mdl = instance_ref()
            if mdl:  # if not yet garbage collected
                mdl.setattr(field_name, mdl_instance)

    def _create_one_to_many(self, source_mdl, target_mdl, listnode_name=None, verbose_name=None):
        # other side of n-to-many should be a ListNode
        # with our source model as the sole element
        if not listnode_name:
            listnode_name = '%s_set' % un_camel(source_mdl.__name__)
        from .listnode import ListNode
        source_instance = source_mdl()
        source_instance.setattrs(_is_auto_created=True)
        # create a new class which extends ListNode
        listnode = type(listnode_name, (ListNode,),
                        {un_camel(source_mdl.__name__): source_instance,
                         '_is_auto_created': True})
        target_mdl._nodes[listnode_name] = listnode
        # add just created model_set to model instances that
        # initialized inside of another model as linked model
        for instance_ref in target_mdl._instance_registry:
            mdl = instance_ref()
            if mdl:  # if not yet garbage collected
                mdl._instantiate_node(listnode_name, listnode)

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
