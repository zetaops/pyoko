# -*-  coding: utf-8 -*-
"""
riak client configuration
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

import riak
# from riak.security import SecurityCreds
from pyoko.conf import settings


# creds = SecurityCreds(username='esat', password='qwe-asd', cacert_file='riak.crt')
# client = riak.RiakClient(protocol='pbc', host=SERVER_IP, pb_port='8087', credentials=creds)

pbc_client = riak.RiakClient(protocol='pbc', host=settings.RIAK_IP, pb_port='8087')
http_client = riak.RiakClient(protocol='http', host=settings.RIAK_IP, http_port='8098')

