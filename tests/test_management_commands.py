# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.


# FIXME: schema update/creation runs multithreaded
# if we run this -fake- test before other db related ones,
# we can be sure that it's working as expected.
from time import sleep

from pyoko.manage import ManagementCommands


def taest_apply_solr_schema():
    mc = ManagementCommands(args=['migrate', '--model', 'Student', '--force'])
    # sleep(10)
    # mc.parse_args()
    # mc.schema_update()
    # sleep(20)  # riak probably will need some time to apply schema updates
    # to other nodes. but we need to investigate how much time required
    #

def taest_load_dump_data():
    try:
        from io import BytesIO as io
    except:
        from cStringIO import StringIO as io
    import sys

    sys.stdout = io()

    # blah blah lots of code ...

    ManagementCommands(args=['dump_data', '--model', 'Student'])
    sys.stdout.seek(0)
    output = sys.stdout.read()
    sys.stdout = sys.__stdout__
    path = '/tmp/load_dump.csv'
    with open(path,'w') as out:
        out.write(output)
    ManagementCommands(args=['load_data', '--update', '--file', path])

    sleep(1)
    sys.stdout = io()
    ManagementCommands(args=['dump_data', '--model', 'Student'])
    sys.stdout.seek(0)
    last_output = sys.stdout.read()
    sys.stdout = sys.__stdout__
    assert output == last_output
    # sleep(20)


