# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from copy import deepcopy
from tests.data.test_data import data, clean_data
from tests.models import Student


def test_save_load_model():
    st = Student()
    st._load_data(data)
    st.save()
    key = st.key
    st2 = Student.objects.get(key=key)
    clean_value = st2.clean_value()
    clean_data['timestamp'] = clean_value['timestamp']
    assert clean_data == clean_value

