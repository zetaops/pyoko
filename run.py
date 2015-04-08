#!/usr/bin/env python
# -*-  coding: utf-8 -*-
"""
./run.py method_name execution_count
./run.py save_students 1000
./run.py multi_save_students 1
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

import timeit
import sys
print sys.argv

test_method = sys.argv[1]
test_count = int(sys.argv[2]) if len(sys.argv) == 3 else 1000

print timeit.timeit('%s()' % test_method, 'from test_methods import %s' % test_method, number=test_count)