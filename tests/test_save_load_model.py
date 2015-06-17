# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from time import sleep
from tests.data.test_data import data, clean_data, solr_doc
from tests.models import Student


class TestDBRelations:
    """
    For the sake of DRY and to speedup tests, we're running clear_bucket
    only once at first test, then creating a new object and reusing it.
    """
    cleaned_up = False
    new_obj = None

    @classmethod
    def clear_bucket(cls):
        if not cls.cleaned_up:
            Student.objects._clear_bucket()
            cls.cleaned_up = True

    @classmethod
    def get_or_create_new_obj(cls):
        if cls.new_obj is None:
            cls.new_obj = Student()
            cls.new_obj._load_data(data)
            cls.new_obj.save()
            sleep(1)  # wait for Riak -> Solr sync
        return cls.new_obj

    def test_save_load_model(self):
        self.clear_bucket()
        st = self.get_or_create_new_obj()
        key = st.key
        st2 = Student.objects.get(key=key)
        clean_value = st2.clean_value()
        clean_data['timestamp'] = clean_value['timestamp']
        assert clean_data == clean_value

    def test_save_query_get_first(self):
        self.clear_bucket()
        self.get_or_create_new_obj()
        st2 = Student.objects.filter(
            auth_info__email=data['auth_info']['email'])[0]
        clean_value = st2.clean_value()
        clean_data['timestamp'] = clean_value['timestamp']
        assert clean_data == clean_value

    def test_save_query_list_models(self):
        self.clear_bucket()
        self.get_or_create_new_obj()
        students = list(Student.objects.filter(
            auth_info__email=data['auth_info']['email']))
        st2 = students[0]
        clean_value = st2.clean_value()
        clean_data['timestamp'] = clean_value['timestamp']
        assert clean_data == clean_value

    def test_save_query_list_riak_objects(self):
        self.clear_bucket()
        self.get_or_create_new_obj()
        students = list(Student.objects.data().filter(
            auth_info__email=data['auth_info']['email']))
        st2_data = students[0].data
        clean_data['timestamp'] = st2_data['timestamp']
        assert clean_data == st2_data

    def test_save_query_list_solr_docs(self):
        self.clear_bucket()
        st = self.get_or_create_new_obj()
        st2_doc = list(Student.objects.solr().filter(
            auth_info__email=data['auth_info']['email']))[0]
        solr_doc['timestamp'] = st2_doc['timestamp']
        solr_doc['_yz_id'] = st2_doc['_yz_id']
        solr_doc['score'] = st2_doc['score']
        solr_doc['_yz_rk'] = st.key
        assert solr_doc == st2_doc
