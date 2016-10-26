# -*-  coding: utf-8 -*-
"""
riak client configuration
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

import riak
from pyoko.conf import settings

from redis import Redis

redis_host, redis_port = settings.REDIS_SERVER.split(':')
cache = Redis(redis_host, redis_port)

client = riak.RiakClient(protocol=settings.RIAK_PROTOCOL,
                         host=settings.RIAK_SERVER,
                         http_port=settings.RIAK_PORT)

log_bucket = client.bucket_type(
    settings.VERSION_LOG_BUCKET_TYPE).bucket(settings.ACTIVITY_LOGGING_BUCKET)

version_bucket = client.bucket_type(
    settings.VERSION_LOG_BUCKET_TYPE).bucket(settings.VERSION_BUCKET)