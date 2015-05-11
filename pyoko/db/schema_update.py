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

field_template = '<field type="{type}" name="{name}"  indexed="{index}" stored="{store}" multiValued="{multi}" />'

class SchemaUpdater(object):
    def __init__(self, registry, dry_run=False):
        for klass in registry.registry:
            ins = klass()
            self.dry_run = dry_run
            self.create_schema(ins._collect_index_fields(), ins._get_bucket_name())


    def create_schema(self, fields, schema_name):
        """

        :param fields: bucket list(('name','string',False), ('age','int',False),
        ('lectures.name', 'string', True))
        :param schema_name: string
        :return: None
        """
        pth = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        with open("%s/solr_schema_template.xml" % pth, 'r') as fh:
            schema_template = fh.read()
        add_to_schema = []
        for name, field_type, solr_type, index, store, multi in fields:
            typ = solr_type or field_type
            add_to_schema.append(field_template.format(name=name,
                                                       type=typ,
                                                       index=index,
                                                       store=store,
                                                       multi=multi).lower())
        new_schema = schema_template.format('\n'.join(add_to_schema))
        print '\n'.join(add_to_schema)
        if not self.dry_run:
            http_client.create_search_schema(schema_name, new_schema)

