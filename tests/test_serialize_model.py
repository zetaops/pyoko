# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.


from tests.data.test_data import data, clean_data
from tests.models import Student


def sort_it(dct, k_sk):
    """
    :param (('','')) k_v: key, sub_key ie: ('lectures', 'code')
    """
    for key, sub_key in k_sk:
        dct[key] = sorted(dct[key], key=lambda x: x[sub_key])
    return dct


# clean_data = sort_it(clean_data, (('lectures','code'),))


# def model_to_json_compact():
def test_model_to_json_compact():
    st = Student(**data)
    st.join_date = data['join_date']
    st.AuthInfo(**data['auth_info'])
    for lct_data in data['lectures']:
        lecture = st.Lectures(**lct_data)
        lecture.NodeInListNode(**lct_data['node_in_list_node'])
        for atd in lct_data['attendance']:
            lecture.Attendance.add(**atd)
        for exam in lct_data['exams']:
            lecture.Exams(**exam)
    # print st.clean_value()
    clean_value = st.clean_value()
    clean_data['timestamp'] = clean_value['timestamp']
    assert clean_data == clean_value


# def test_mode8l_to_json_compact(benchmark):
#     benchmark(model_to_json_compact )



def test_model_to_json_expanded():
    d = data
    s = Student()
    s.number = d['number']
    s.deleted = d['deleted']
    # s.timestamp = d['timestamp']
    s.bio = d['bio']
    s.name = d['name']
    s.surname = d['surname']
    s.pno = d['pno']
    s.join_date = data['join_date']
    d = data['auth_info']
    ai = s.AuthInfo()
    ai.email = d['email']
    ai.password = d['password']
    ai.username = d['username']
    for ld in data['lectures']:
        lecture = s.Lectures()
        lecture.code = ld['code']
        lecture.credit = ld['credit']
        lecture.name = ld['name']
        milm = lecture.NodeInListNode()
        milm.foo = ld['node_in_list_node']['foo']
        for atd in ld['attendance']:
            attendance = lecture.Attendance()
            attendance.attended = atd['attended']
            attendance.date = atd['date']
            attendance.hour = atd['hour']
        for exam in ld['exams']:
            exm = lecture.Exams()
            exm.date = exam['date']
            exm.point = exam['point']
            exm.type = exam['type']
    clean_value = s.clean_value()
    clean_data['timestamp'] = clean_value['timestamp']
    assert clean_data == clean_value
