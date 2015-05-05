# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

class PyokoError(Exception):
    pass


class ValidationError(PyokoError):
    pass


class NoSuchObjectError(PyokoError):
    pass

class MultipleObjectsReturned(PyokoError):
    """The query returned multiple objects when only one was expected."""
    pass
