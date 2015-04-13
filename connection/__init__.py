# -*-  coding: utf-8 -*-
"""
riak client configuration
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

import riak
from riak.security import SecurityCreds
from local_settings import SERVER_IP


creds = SecurityCreds(username='esat', password='qwe-asd', cacert_file='riak.crt')
# client = riak.RiakClient(protocol='pbc', host=SERVER_IP, pb_port='8087', credentials=creds)
client = riak.RiakClient(protocol='pbc', host=SERVER_IP, pb_port='8087')
# client = riak.RiakClient(protocol='http', host=SERVER_IP, http_port='8098')
# client =