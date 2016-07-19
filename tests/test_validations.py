# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import pytest
from .models import AbstractRole

from pyoko.exceptions import ValidationError
from tests.models import User, Role, Permission


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


    def test_raise_assign_to_nodes(self):
        with pytest.raises(ValidationError):
            r = AbstractRole()
            p = Permission()
            r.Permissions = p

        with pytest.raises(ValidationError):
            r = AbstractRole()
            r.Permissions = 'Foo'

        with pytest.raises(ValidationError):
            r = Role()
            p = Permission()
            r.usr = p

        with pytest.raises(ValidationError):
            r = Role()
            r.usr = 'Foo'

        r = Role()
        u = User()
        r.usr = u






















