# -*-  coding: utf-8 -*-
"""
this module contains a base class for other db access classes
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from collections import defaultdict
from enum import Enum
import sys
ReturnType = Enum('ReturnType', 'Solr Object Model')
sys.PYOKO_STAT_COUNTER = {
    "save": 0,
    "update": 0,
    "read": 0,
    "count": 0,
    "search": 0,
}
sys.PYOKO_LOGS = defaultdict(list)

class BaseAdapter(object):
    """
    QuerySet is a lazy data access layer for Riak.
    """

    def __init__(self, **conf):
        self._current_context = None
        self._pre_compiled_query = ''
        # pass permission checks to genareted model instances
        self._pass_perm_checks = False
        self._cfg = {'row_size': 1000,
                     'rtype': ReturnType.Model}
        self._cfg.update(conf)
        self._model = None
        self.is_clone = False
