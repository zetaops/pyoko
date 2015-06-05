# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import os
import sys
from pyoko.manage import ManagementCommands

os.environ.setdefault('PYOKO_SETTINGS', 'tests.settings')

if __name__ == '__main__':

    ManagementCommands(sys.argv[1:])

