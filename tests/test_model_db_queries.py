# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from time import sleep
import pytest
from pyoko.conf import settings
from pyoko.exceptions import MultipleObjectsReturned
from pyoko.manage import ManagementCommands, FlushDB
from tests.data.test_data import data, clean_data
from tests.models import Student, TimeTable


class TestCase:
    """
    For the sake of DRY and to speedup tests, we're running clear_bucket
    only once at first test, then creating a new object and reusing it.
    """
    cleaned_up = False
    new_obj = None

    @classmethod
    def clear_bucket(cls, reset):
        if not cls.cleaned_up or reset:
            FlushDB(model='Student,TimeTable').run()
            cls.cleaned_up = True

    @classmethod
    def get_or_create_new_obj(cls, reset):
        if cls.new_obj is None or reset:
            cls.new_obj = Student()
            cls.new_obj.set_data(data)
            cls.new_obj.save()
            sleep(1)  # wait for Riak -> Solr sync
        return cls.new_obj

    @classmethod
    def prepare_testbed(cls, reset=False):
        cls.clear_bucket(reset)
        return cls.get_or_create_new_obj(reset)

    def test_listnode_values(self):
        st = Student()
        l = st.Lectures(code='Mat101')
        l.credit = 4
        assert l.code == 'Mat101'
        assert l.credit == 4
        st.save()
        db_st = Student.objects.get(st.key)
        db_l = db_st.Lectures[0]
        assert l.credit == db_l.credit
        assert l.code == db_l.code

    def test_save_load_model(self):
        st = self.prepare_testbed()
        key = st.key
        st2 = Student.objects.get(key)
        clean_value = st2.clean_value()
        clean_data['timestamp'] = clean_value['timestamp']
        clean_data['updated_at'] = clean_value['updated_at']
        assert clean_data == clean_value

    def test_get_multiple_objects_exception(self):
        self.prepare_testbed()
        s2 = Student(name='Foo').save()
        sleep(2)
        with pytest.raises(MultipleObjectsReturned):
            Student.objects.get()

    def test_delete_model(self):
        self.prepare_testbed(True)
        s2 = Student(name='Foo').save()
        sleep(2)
        assert Student.objects.filter(name='Foo').count() == 1
        assert Student.objects.filter(deleted=True).count() == 0
        assert Student.objects.count() == 2
        s2.delete()
        sleep(1)
        assert Student.objects.filter(name='Foo').count() == 0
        assert Student.objects.filter(deleted=True).count() == 1
        assert Student.objects.count() == 1

    def test_filter(self):
        # filter by name, if name not equals filtered names then append to list
        self.prepare_testbed()
        filter_result = [s.name for s in Student.objects.filter(name='Jack') if
                         s.name != 'Jack']

        assert len(filter_result) == 0

    def test_riak_raw_query(self):
        self.prepare_testbed()
        assert 'Jack' == Student.objects.raw('name:Jack').get().name
        qset = Student.objects.raw('name:Jack').set_params(rows=0)
        qset.adapter._exec_query()
        no_row_result = qset.adapter._solr_cache
        assert no_row_result['docs'] == []
        assert no_row_result['num_found'] == 1
        st_queryset = Student.objects.raw('name:Nope')
        st_list = list(st_queryset)
        assert not bool(st_list)

    def test_exclude(self):
        # exclude by name, if name equals filtered names then append to list
        self.prepare_testbed()
        exclude_result = [s.name for s in Student.objects.exclude(name='Jack')
                          if s.name == 'Jack']

        assert len(exclude_result) == 0

    def test_save_query_get_first(self):
        self.prepare_testbed()
        st2 = Student.objects.filter(
                auth_info__email=data['auth_info']['email'])[0]
        clean_value = st2.clean_value()
        clean_data['timestamp'] = clean_value['timestamp']
        clean_data['updated_at'] = clean_value['updated_at']
        assert clean_data == clean_value

    def test_save_query_list_models(self):
        self.prepare_testbed()
        students = Student.objects.filter(
                auth_info__email=data['auth_info']['email'])
        st2 = students[0]
        clean_value = st2.clean_value()
        clean_data['timestamp'] = clean_value['timestamp']
        clean_data['updated_at'] = clean_value['updated_at']
        assert clean_data == clean_value

    def test_save_query_list_riak_objects(self):
        self.prepare_testbed()
        students = Student.objects.data().filter(
                auth_info__email=data['auth_info']['email'])
        st2_data = students[0][0]
        clean_data['timestamp'] = st2_data['timestamp']
        clean_data['updated_at'] = st2_data['updated_at']
        clean_data['deleted_at'] = st2_data['deleted_at']

        assert clean_data == st2_data

    def test_riak_save_query_list_solr_docs(self):
        # FIXME: order of multivalued field values varies between solr versions
        st = self.prepare_testbed()
        qset = Student.objects.filter(auth_info__email=data['auth_info']['email'])
        qset.adapter._exec_query()
        st2_doc = qset.adapter._solr_cache['docs'][0]
        assert st2_doc['_yz_rb'] == 'student'
        assert st2_doc['_yz_rt'] == settings.DEFAULT_BUCKET_TYPE
        assert st2_doc['_yz_rk'] == st.key

    def test_lte_gte(self):
        self.prepare_testbed()
        TimeTable(week_day=4, hours=2).save()
        TimeTable(week_day=2, hours=4).save()
        TimeTable(week_day=5, hours=1).save()
        TimeTable(week_day=3, hours=6).save()
        sleep(1)
        assert TimeTable.objects.filter(hours__gte=4).count() == 2
        assert TimeTable.objects.filter(hours__lte=4).count() == 3

    def test_or_queries(self):
        d = {'s1': ['ali', 'veli'],
             's2': ['joe', 'roby'],
             's3': ['rob', 'zombie'],
             's4': ['go', 'jira']}
        if not Student.objects.filter(name=d['s2'][0]):
            for k, v in d.items():
                Student(name=v[0], surname=v[1]).save()
            sleep(1)
        assert 3 == Student.objects.filter(
                name__in=(d['s1'][0], d['s2'][0], d['s3'][0])).count()

        assert 3 == Student.objects.filter(
                name__in=(d['s1'][0], d['s2'][0], d['s3'][0])).filter(
                surname__in=(d['s1'][1], d['s2'][1], d['s3'][1])).count()

        assert 2 == Student.objects.search_on('name', 'surname', contains='rob').count()
        assert 2 == Student.objects.or_filter(name__contains='rob',
                                              surname__startswith='rob').count()
