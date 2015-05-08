# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from pyoko.db.solriakcess import SolRiakcess


class Student(SolRiakcess):
    """
    contains common db access patterns for Student bucket
    usage:
    st = Student()
    st.by_pno('10623465730').get()
    st.by_city('Kon*').all()


    In [2]: st.with_unpaid_fees().count()
    Out[2]: 818

    In [3]: st.with_unpaid_fees().by_city('Ar*').count()
    Out[3]: 7

    In [4]: st.with_unpaid_fees().by_city('Ar*').get()
    ~~~~ MultipleObjectsReturned Exception
    """
    def __init__(self, **kwargs):
        super(Student, self).__init__(**kwargs)
        self._cfg.index = 'student2'
        self.set_bucket('student', 'student5')


    def by_id(self, student_id):
        return self.bucket.get(str(student_id))

    def by_pno(self, student_id):
        return self.filter(identity_information__tc_no_l=student_id)


    def by_city(self, city):
        return self.filter(contact_information__addresses__city_ss=city)


    def with_unpaid_fees(self):
        return self.filter(payment_information__tuition_fees__unpaid_ss=None)


if __name__ == '__main__':
    from connection import http_client
    st = Student(client=http_client)
    # s = copy.deepcopy(st)
    # print st.by_city('A*').watch(1)[1]
    # print len(list(st.by_city('A*').watch(1)))
    at = st.by_city('S*')
    print len(list(at.w()))
    # print list(st.by_city('Ak*').all())
    # print list(st.by_city('Ak*').all())
    print(st)
