# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.


from tests.data.test_data import data
from tests.models import Student





# def model_to_json_compact():
def test_model_to_json_compact():
    st = Student(**data)
    st.join_date = data['join_date']
    st.AuthInfo(**data['AuthInfo'])
    for lct_data in data['Lectures']:
        lecture = st.Lectures(**lct_data)
        lecture.NodeInListNode(**lct_data['NodeInListNode'])
        for atd in lct_data['Attendance']:
            lecture.Attendance(**atd)
        for exam in lct_data['Exams']:
            lecture.Exams(**exam)
    # print st.clean_value()
    clean_value  = st.clean_value()
    data['timestamp'] = clean_value['timestamp']
    assert data == clean_value

# def test_mode8l_to_json_compact(benchmark):
#     benchmark(model_to_json_compact )



def test_model_to_json_expanded():
    d = data
    s = Student()
    s.number = d['number']
    s._deleted = d['_deleted']
    s.archived = d['archived']
    s.timestamp = d['timestamp']
    s.bio = d['bio']
    s.name = d['name']
    s.surname = d['surname']
    s.pno = d['pno']
    s.join_date = data['join_date']
    d = data['AuthInfo']
    ai = s.AuthInfo()
    ai.email = d['email']
    ai.password = d['password']
    ai.username = d['username']
    for ld in data['Lectures']:
        lecture = s.Lectures()
        lecture.code = ld['code']
        lecture.credit = ld['credit']
        lecture.name = ld['name']
        milm = lecture.NodeInListNode()
        milm.foo = ld['NodeInListNode']['foo']
        for atd in ld['Attendance']:
            attendance = lecture.Attendance()
            attendance.attended = atd['attended']
            attendance.date = atd['date']
            attendance.hour = atd['hour']
        for exam in ld['Exams']:
            exm = lecture.Exams()
            exm.date = exam['date']
            exm.point = exam['point']
            exm.type = exam['type']
    clean_data = s.clean_value()
    assert data == clean_data
