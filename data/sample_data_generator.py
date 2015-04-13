# -*-  coding: utf-8 -*-
"""
test data generator
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import json

__author__ = 'evren'

from schemas import make_student_data

open("sample_fake_student_object.json", 'w').write(json.dumps(make_student_data(), ensure_ascii=False).encode('utf8'))