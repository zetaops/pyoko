# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.


from tests.data.test_data import data
from tests.models import Student


def test_json_to_model_to_json():
    st = Student()
    st._load_data(data)
    clean_value = st.clean_value()
    data['timestamp'] = clean_value['timestamp']
    assert data == clean_value
