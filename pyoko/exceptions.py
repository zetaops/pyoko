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

class NotCompatible(PyokoError):
    """Incorrect usage of method / function"""
    pass

class MultipleObjectsReturned(PyokoError):
    """The query returned multiple objects when only one was expected."""
    pass

class ObjectDoesNotExist(PyokoError):
    pass

class IntegrityError(PyokoError):
    """raised on unique/unique_together mismatches"""
    pass
