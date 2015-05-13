# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from pyoko.db.connection import http_client
# from pyoko.db.solr_schema_fields import SOLR_FIELDS
import os, inspect




class SchemaUpdater(object):
    """
    traverses trough all models, collects fields marked for index or store in solr
    then creates a solr schema for these fields.
    """

    FIELD_TMP = '<field type="{type}" name="{name}"  indexed="{index}" stored="{store}" multiValued="{multi}" />'

    def __init__(self, registry):
        self.registry = registry

    def run(self):
        for klass in self.registry.registry:
            ins = klass()
            fields = self.create_schema(ins._collect_index_fields())
            self.apply_schema(fields, ins._get_bucket_name())

    @classmethod
    def create_schema(cls, fields):
        """
        :param fields: bucket list(('name','string',False), ('age','int',False),
        ('lectures.name', 'string', True))
        :param schema_name: string
        :return: None
        """
        return [cls.FIELD_TMP.format(name=name,
                                      type=solr_type or field_type,
                                      index=index,
                                      store=store,
                                      multi=multi).lower()
                for name, field_type, solr_type, index, store, multi in fields]

    def apply_schema(self, fields, schema_name):
        pth = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        with open("%s/solr_schema_template.xml" % pth, 'r') as fh:
            schema_template = fh.read()
        new_schema = schema_template.format('\n'.join(fields))
        http_client.create_search_schema(schema_name, new_schema)
