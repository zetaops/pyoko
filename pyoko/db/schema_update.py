# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import codecs
import six
from pyoko.db.connection import http_client as client
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
        self.client = client

    def run(self):
        for klass in self.registry.get_base_models():
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
        return [cls.FIELD_TMP.format(name=name.lower(),
                                      type=(solr_type or field_type).lower(),
                                      index=str(index).lower(),
                                      store=str(store).lower(),
                                      multi=str(multi).lower())
                for name, field_type, solr_type, index, store, multi in fields]

    def apply_schema(self, fields, schema_name):
        pth = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        with codecs.open("%s/solr_schema_template.xml" % pth, 'r', 'utf-8') as fh:
            schema_template = fh.read()
        new_schema = schema_template.format('\n'.join(fields)).encode('utf-8')

        self.client.create_search_schema(schema_name, new_schema)
        print(new_schema)
        self.client.create_search_index(schema_name, schema_name)
        b = self.client.bucket(schema_name)
        b.set_property('search_index', schema_name)
