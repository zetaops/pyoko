#!/usr/bin/env python
# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

from pyoko.manage import *

# class MyCmd(Command):
#     CMD_NAME = 'mycommand'
#     PARAMS = [('my_param', True, 'Example description')]
#
#
#     def run(self):
#         import os
#         self.manager.report = os.popen('ls -lah').read()


environ.setdefault('PYOKO_SETTINGS', 'tests.settings')
ManagementCommands(argv[1:]) # , commands=[MyCmd]
