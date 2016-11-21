# -*-  coding: utf-8 -*-
# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
"""
Default Settings
"""
import os

DEFAULT_BUCKET_TYPE = os.environ.get('DEFAULT_BUCKET_TYPE', 'pyoko_models')
# write_once bucket doesn't support secondary indexes. Thus, backend is defined
# as "leveldb_mult" in log_version bucket properties.
VERSION_LOG_BUCKET_TYPE = os.environ.get('VERSION_LOG_BUCKET_TYPE', 'log_version')

RIAK_SERVER = os.environ.get('RIAK_SERVER', 'localhost')
RIAK_PROTOCOL = os.environ.get('RIAK_PROTOCOL', 'http')
RIAK_PORT = os.environ.get('RIAK_PORT', 8098)

#: Redis address and port.
REDIS_SERVER = os.environ.get('REDIS_SERVER', '127.0.0.1:6379')

#: Redis password (password).
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)

#: Set True to enable versioning on write-once buckets
ENABLE_VERSIONS = os.environ.get('ENABLE_VERSIONS', 'False') == 'True'

#: Suffix for version buckets
VERSION_SUFFIX = os.environ.get('VERSION_SUFFIX', '_version')

#: Set True to enable auto-logging of all DB operations to a
#: write-once log bucket
ENABLE_ACTIVITY_LOGGING = os.environ.get('ENABLE_ACTIVITY_LOGGING', 'False') == 'True'

#: Set the name of logging bucket type and bucket name.
ACTIVITY_LOGGING_BUCKET = os.environ.get('ACTIVITY_LOGGING_BUCKET', 'log')
VERSION_BUCKET = os.environ.get('VERSION_BUCKET', 'version')
