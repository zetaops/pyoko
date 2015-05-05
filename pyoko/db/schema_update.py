# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from pyoko.db.connection import http_client
from pyoko.db.solr_schema_fields import SOLR_FIELDS
import os, inspect

class SchemaUpdater(object):
    def __init__(self, registry):
        for klass in registry.registry:
            ins = klass()
            self.create_schema(ins.collect_index_fields(), ins._get_bucket_name())


    def create_schema(self, fields, schema_name):
        """

        :param fields: bucket list(('name','string',False), ('age','int',False),
        ('lectures.name', 'string', True))
        :param schema_name: string
        :return: None
        """
        pth = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        schema_template = open("%s/solr_schema_template.xml" % pth, 'r').read()
        add_to_schema = []

        for field_name, field_type, multi in fields:
            multi_value = 'true' if multi else 'false'
            if field_type in SOLR_FIELDS:
                add_to_schema.append(SOLR_FIELDS[field_type] % (field_name, multi_value))
            else:
                add_to_schema.append(SOLR_FIELDS['local'] % (field_type, multi_value))
        new_schema = schema_template.format('\n'.join(add_to_schema))
        print new_schema
        # http_client.create_search_schema(schema_name, new_schema)

