# -*-  coding: utf-8 -*-
"""
data models for tests
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import datetime
import time
from test_model import *

lecture_data = {
    'math101':{
        'name': 'Introduction to Math',
        'code': 'math101',
        'credit': 4
    },
    'rock101':{
        'name': 'Introduction to Rocking',
        'code': 'rock101',
        'credit': 10,
    }
}

student_data = [
    {
        'name': "Jack",
        'surname': "Black",
        'pno': "2343243433",
        'number': "20300344",
        'lectures': ['math101', 'rock101'],
        'attendance':[]
    },
]

# if __file__ == '__main__':
t1 = time.time()
s = student_data[0]
for i in range(1):
    st = Student(**s)
    st.join_date = datetime.date.today()
    st.AuthInfo(username='foo_user', email='suuper@suup.com', password='123')
    for l in s['lectures']:
        l = lecture_data[l]
        lecture = st.Lectures(**l)
        lecture.ModelInListModel(foo='FOOOO')
        lecture.Attendance.add(date=datetime.date.today(), hour=2, attended=False)
        lecture.Attendance.add(date=datetime.date.today(), hour=4, attended=True)
        lecture.Exams.add(date=datetime.date.today(), type='Q', point=65)
ctime = "Object creation : %s ms" % round(time.time() - t1, 5)
t2 = time.time()
# st.save()
print ctime, "\n", "Data collection : %s ms" % round(time.time() - t2, 5)

# qs = Student.objects.filter(name='Jack',lectures__attandance__attended=False)

    # Student.objects
