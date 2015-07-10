# -*-  coding: utf-8 -*-
"""
project settings for a pyoko based example project
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import os

RIAK_SERVER = os.environ.get('RIAK_SERVER')
RIAK_PROTOCOL = os.environ.get('RIAK_PROTOCOL')
RIAK_PORT = os.environ.get('RIAK_PORT')

if not RIAK_SERVER:
    RIAK_SERVER = 'localhost'
if not RIAK_PROTOCOL:
    RIAK_PROTOCOL = 'http'
if not RIAK_PORT:
    RIAK_PORT = '8098'

DEFAULT_BUCKET_TYPE = 'pyoko_models'

# MODELS_MODULE = '<PYTHON.PATH.OF.MODELS.MODULE>'
