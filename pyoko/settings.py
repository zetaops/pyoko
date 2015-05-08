# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

#### Storage Strategy for Solr. ####
# By default, if it's not explicitly excluded,
# we're storing all (except Text) fields in Solr,
# no matter if they are indexed or not.

SOLR_STORE_ALL = True
