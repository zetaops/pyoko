# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import pytest

from tests.models import User

# class FF(object):
#     def __init__(self):
#         self.__class__.__setattr__ = self._sattr
#
#     def _sattr(self, key, val):
#         print(key, val)
#         object.__setattr__(self, key, val)
#
# f = FF()
#
# f.a = 'b'
# print(f.__class__.__dict__)

class TestCase:
    """
    contains various field - data validation tests
    """

    def test_raise_assign_to_non_existent_field(self):
        with pytest.raises(AttributeError):
            u = User()
            u.foo = 'bar'






















