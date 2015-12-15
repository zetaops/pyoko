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


class Registry(object):
    def __init__(self):
        self.registry = {}
        self.lazy_models = defaultdict(list)
        self.app_registry = defaultdict(dict)
        # self.link_registry = defaultdict(list)

    def register_model(self, mdl):
        if mdl not in self.registry:
            self.registry[mdl.__name__] = mdl
            self.app_registry[mdl.Meta.app][mdl.__name__] = mdl
            self._process_links_from_nodes_of_mdl(mdl)
            self._pre_process_lazy_links(mdl)
            self._process_links(mdl)

    def _process_links(self, mdl):
        for lnk in mdl.get_links():
            # custom reverse name or model name if one to one
            # or model_name_set otherwise
            reverse_name = un_camel(
                    lnk['reverse'] or mdl.__name__ + ('' if lnk['o2o'] else '_set'))
            # self.link_registry[lnk['mdl']].append((name, mdl, reverse_name))
            if lnk['o2o']:
                self._create_one_to_one(mdl,
                                        lnk['mdl'],
                                        reverse_name)
                lnk['mdl']._add_linked_model(mdl,
                                             o2o=True,
                                             field=reverse_name)
            else:
                lnk['mdl']._add_linked_model(mdl,
                                             reverse=lnk['field'],
                                             field=reverse_name, is_set=True)
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
                target_mdl._add_linked_model(mdl,
                                      reverse=lm['reverse'],
                                      field=lm['field'])
                mdl._add_linked_model(target_mdl,
                                      reverse=lm['field'],
                                      field=lm['reverse'],
                                      is_set=True)
                self._create_one_to_many(target_mdl, mdl, lm['reverse'])
                setattr(target_mdl, lm['field'], mdl)

    def _process_links_from_nodes_of_mdl(self, source_mdl):
        # print("Node: %s" % source_mdl.__name__)
        for node in source_mdl._nodes.values():
            for lnk in node.get_links():
                reverse_name = un_camel(
                        lnk['reverse'] or source_mdl.__name__ + ('' if lnk['o2o'] else '_set'))
                if not lnk['o2o']:
                    lnk['mdl']._add_linked_model(source_mdl,
                                                 o2o=False,
                                                 field=reverse_name,
                                                 reverse=lnk['field'],
                                                 is_set=True)
                    self._create_one_to_many(source_mdl,
                                             target_mdl=lnk['mdl'],
                                             listnode_name=lnk['reverse'])
                else:

                    lnk['mdl']._add_linked_model(source_mdl,
                                                 o2o=True,
                                                 field=reverse_name,
                                                 reverse=lnk['field'])
                    self._create_one_to_one(source_mdl,
                                            target_mdl=lnk['mdl'],
                                            field_name=reverse_name)

    def _create_one_to_one(self, source_mdl, target_mdl, field_name):
        mdl_instance = source_mdl(one_to_one=True)
        mdl_instance._is_auto_created = True
        for instance_ref in target_mdl._instance_registry:
            mdl = instance_ref()
            if mdl:  # if not yet garbage collected
                setattr(mdl, field_name, mdl_instance)
                # target_mdl._add_linked_model(source_mdl, o2o=True, field=field_name)

    def _create_one_to_many(self, source_mdl, target_mdl, listnode_name=None):
        # other side of n-to-many should be a ListNode
        # with our source model as the sole element
        if not listnode_name:
            listnode_name = '%s_set' % un_camel(source_mdl.__name__)
        from .listnode import ListNode
        source_instance = source_mdl()
        source_instance._is_auto_created = True
        # create a new class which extends ListNode
        listnode = type(listnode_name, (ListNode,),
                        {un_camel(source_mdl.__name__): source_instance,
                         '_is_auto_created': True})
        # listnode._add_linked_model(source_mdl, o2o=False, field=listnode_name,
        #                            reverse=un_camel(source_mdl.__name__), offff=target_mdl)
        # source_mdl._add_linked_model(target_mdl, o2o=False, )
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
