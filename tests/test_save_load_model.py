# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from copy import deepcopy
from time import sleep
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

def test_save_query_get_first():
    # Student.objects._clear_bucket()
    st = Student()
    st._load_data(data)
    st.save()
    sleep(1)
    st2 = Student.objects.filter(auth_info__email=data['auth_info']['email']).w()[0]
    clean_value = st2.clean_value()
    clean_data['timestamp'] = clean_value['timestamp']
    assert clean_data == clean_value

