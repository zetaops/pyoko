# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from lib.db.base import RiakDataAccess


class Students(RiakDataAccess):

    def __init__(self, riak_client, light=True):
        super(Students, self).__init__(riak_client, just_indexed_data=light)


    def by_id(self, student_id):
        return self.bucket.get(student_id)

    def by_city(self, city):
        self.pack_up(self.bucket.search("city_ss:%s" % city, self.index))

    def with_unpaid_fees(self):
        pass

