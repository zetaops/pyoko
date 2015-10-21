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
from pyoko.manage import ManagementCommands
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
            something_deleted = 0
            for mdl in [Student, TimeTable]:
                something_deleted += mdl.objects._clear_bucket()
            cls.cleaned_up = True
            if something_deleted:
                sleep(2)

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



    def test_save_load_model(self):
        st = self.prepare_testbed()
        key = st.key
        st2 = Student.objects.get(key)
        clean_value = st2.clean_value()
        clean_data['timestamp'] = clean_value['timestamp']
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
        sleep(1)
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

    def test_raw_query(self):
        self.prepare_testbed()
        assert 'Jack' == Student.objects.raw('name:Jack').get().name
        no_row_result = Student.objects.raw('name:Jack', rows=0)._exec_query()._solr_cache
        assert no_row_result['docs'] == []
        assert no_row_result['num_found'] == 1
        assert not bool(list(Student.objects.raw('name:Nope')))

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
        assert clean_data == clean_value

    def test_save_query_list_models(self):
        self.prepare_testbed()
        students = Student.objects.filter(
            auth_info__email=data['auth_info']['email'])
        st2 = students[0]
        clean_value = st2.clean_value()
        clean_data['timestamp'] = clean_value['timestamp']
        assert clean_data == clean_value

    def test_save_query_list_riak_objects(self):
        self.prepare_testbed()
        students = Student.objects.data().filter(
            auth_info__email=data['auth_info']['email'])
        st2_data = students[0].data
        clean_data['timestamp'] = st2_data['timestamp']
        assert clean_data == st2_data

    def test_save_query_list_solr_docs(self):
        # FIXME: order of multivalued field values varies between solr versions
        st = self.prepare_testbed()
        st2_doc = Student.objects.solr().filter(
            auth_info__email=data['auth_info']['email'])[0]
        solr_doc = {'_yz_rb': 'student',
                    '_yz_rt': settings.DEFAULT_BUCKET_TYPE,
                    '_yz_id': st2_doc['_yz_id'],
                    'score': st2_doc['score'],
                    '_yz_rk': st.key}
        assert solr_doc == st2_doc


    def test_lte_gte(self):
        self.prepare_testbed()
        TimeTable(week_day=4, hours=2).save()
        TimeTable(week_day=2, hours=4).save()
        TimeTable(week_day=5, hours=1).save()
        TimeTable(week_day=3, hours=6).save()
        sleep(1)
        assert TimeTable.objects.filter(hours_gte=4).count() == 2
        assert TimeTable.objects.filter(hours_lte=4).count() == 3
