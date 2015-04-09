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


creds = SecurityCreds(username='esat', password='qwe-asd', cacert_file='riak.crt')
# client = riak.RiakClient(protocol='pbc', host='62.210.245.199', pb_port='8087', credentials=creds)
client = riak.RiakClient(protocol='pbc', host='62.210.245.199', pb_port='8087')
# client =