# -*-  coding: utf-8 -*-
"""
project settings for a pyoko based example project
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import os
from pyoko.settings import *

RIAK_SERVER = os.environ.get('RIAK_SERVER', 'localhost')
RIAK_PROTOCOL = os.environ.get('RIAK_PROTOCOL', 'http')
RIAK_PORT = os.environ.get('RIAK_PORT', '8098')
DEFAULT_BUCKET_TYPE = os.environ.get('DEFAULT_BUCKET_TYPE', 'pyoko_models')

# MODELS_MODULE = '<PYTHON.PATH.OF.MODELS.MODULE>'


#: Redis address and port.
REDIS_SERVER = os.environ.get('REDIS_SERVER', '127.0.0.1:6379')

#: Redis password (password).
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
