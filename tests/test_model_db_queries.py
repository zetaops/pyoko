# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import datetime
from time import sleep
import pytest
from pyoko.conf import settings
from pyoko.db.adapter.db_riak import BlockSave, BlockDelete, Adapter
from pyoko.exceptions import MultipleObjectsReturned
from pyoko.manage import FlushDB
from tests.data.test_data import data, clean_data
from tests.models import Student, TimeTable, User, Role
from pyoko.db.adapter.base import BaseAdapter
from pyoko.db.connection import client
import time


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
            FlushDB(model='Student,TimeTable', wait_sync=True).run()
            cls.cleaned_up = True

    @classmethod
    def get_or_create_new_obj(cls, reset):
        if cls.new_obj is None or reset:
            cls.new_obj = Student()
            cls.new_obj.set_data(data)
            cls.new_obj.blocking_save()
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
        Student(name='Foo').blocking_save()
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

    def test_all(self):
        mb = client.bucket_type('pyoko_models').bucket('student')
        c = Adapter()._solr_params['sort']
        row_size = BaseAdapter()._cfg['row_size']
        Student.objects._clear()
        assert Student.objects.count() == 0

        for i in range(row_size + 100):
            Student(name=str(i)).save()

        while Student.objects.count() != row_size + 100:
            time.sleep(0.3)

        # Wanted result from filter method much than default row_size.
        # It should raise an exception.
        with pytest.raises(Exception):
            Student.objects.filter()

        # Results are taken from solr in ordered with 'timestamp' sort parameter.
        results = mb.search('-deleted:True', 'pyoko_models_student',
                            **{'sort': 'timestamp desc', 'fl': '_yz_rk, score',
                               'rows': row_size + 100})

        # Ordered key list is created.
        ordered_key_list = [doc['_yz_rk'] for doc in results['docs']]

        # Getting data from riak with unordered way is tested.
        temp_key_list = []
        for s in Student.objects.all():
            temp_key_list.append(s.key)

        assert len(temp_key_list) == row_size + 100
        assert temp_key_list != ordered_key_list

        # Getting data from riak with ordered way is tested.
        temp_key_list = []
        for s in Student.objects.order_by().all():
            temp_key_list.append(s.key)

        assert len(temp_key_list) == row_size + 100
        assert temp_key_list == ordered_key_list
        self.prepare_testbed(reset=True)

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

        assert User.objects.all().exclude(
            name='ThereIsNoSuchAName').count() == User.objects.count()
        assert User.objects.all().exclude(name='Mate2').count() == User.objects.count() - 1
        assert User.objects.filter(name='Mate2').exclude(
            supervisor_id='ThereIsNoSuchAnId').count() == 1
        assert Student.objects.filter(name='Jack').exclude(surname='Black').count() == 0
        assert User.objects.filter(name='Mate2').exclude(name='Mate2').count() == 0

        role_names = ['Foo Fighters']
        assert Role.objects.all().exclude(
            name__in=role_names).count() == Role.objects.count() - 1

        # There are two role with 'Foo Frighters' name and one role with 'Foo Fighters'
        role_names = ['Foo Fighters', 'Foo Frighters']
        assert Role.objects.all().exclude(
            name__in=role_names).count() == Role.objects.count() - 3

        role_keys = Role.objects.filter(name__in=role_names).values_list('key')

        assert Role.objects.filter(active=False).exclude(
            key__in=role_keys).count() == Role.objects.filter(active=False).count() - 3

        assert Role.objects.filter(active__in=[False, True]).exclude(
            key__in=role_keys).count() == Role.objects.filter(active__in=[False, True]).count() - 3

        assert Role.objects.filter(active__in=[False, True], name='Foo Fighters').exclude(
            name__in=['Foo Frighters', 'Nonexistent Fighters']).count() == 1


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

        # fl default is only _yz_rk, score
        qset = Student.objects.set_params(fl='_yz_rk, _yz_rb, _yz_rt, score').filter(auth_info__email=data['auth_info']['email'])
        qset.adapter._exec_query()
        st2_doc = qset.adapter._solr_cache['docs'][0]
        assert st2_doc['_yz_rb'] == 'student'
        assert st2_doc['_yz_rt'] == settings.DEFAULT_BUCKET_TYPE
        assert st2_doc['_yz_rk'] == st.key

    def test_lte_gte(self):
        self.prepare_testbed()
        with BlockSave(TimeTable):
            TimeTable(week_day=4, hours=2).save()
            TimeTable(week_day=2, hours=4).save()
            TimeTable(week_day=5, hours=1).save()
            TimeTable(week_day=3, hours=6).save()
        assert TimeTable.objects.filter(hours__gte=4).count() == 2
        assert TimeTable.objects.filter(hours__lte=4).count() == 3

    def test_lt_gt(self):
        self.prepare_testbed()
        with BlockSave(TimeTable):
            TimeTable.objects.get_or_create(week_day=4, hours=2)
            TimeTable.objects.get_or_create(week_day=2, hours=4)
            TimeTable.objects.get_or_create(week_day=5, hours=1)
            TimeTable.objects.get_or_create(week_day=3, hours=6)
        assert TimeTable.objects.filter(hours__gt=4).count() == 1
        assert TimeTable.objects.filter(hours__lt=4).count() == 2

    def test_slicing(self):
        with BlockDelete(TimeTable):
            TimeTable.objects.delete()
        with BlockSave(TimeTable):
            for i in range(5):
                TimeTable(week_day=i, hours=i).save()
        items = TimeTable.objects.all()[1:2]
        assert len(list(items)) == 1

    def test_or_queries(self):
        Student.objects.delete()
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

    def test_range_queries(self):
        TimeTable.objects.delete()
        with BlockSave(TimeTable):
            TimeTable(week_day=4, hours=2, adate=datetime.date.today(),
                      bdate=datetime.date.today() - datetime.timedelta(days=2)).save()
            TimeTable(week_day=2, hours=4, bdate=datetime.date.today(),
                      adate=datetime.date.today() + datetime.timedelta(2)).save()
            TimeTable(week_day=5, hours=1, adate=datetime.date.today() - datetime.timedelta(1),
                      bdate=datetime.date.today() + datetime.timedelta(12)).save()
            TimeTable(week_day=3, hours=6, adate=datetime.date.today() + datetime.timedelta(10),
                      bdate=datetime.date.today() - datetime.timedelta(2)).save()
        assert TimeTable.objects.filter(week_day__range=[2, 4]).count() == 3
        assert TimeTable.objects.or_filter(week_day__range=[2, 4], hours__range=[1, 4]).count() == 4
        assert TimeTable.objects.or_filter(
            adate__range=(datetime.date.today() - datetime.timedelta(10),
                          datetime.date.today() + datetime.timedelta(10),
                          ), hours__range=[1, 4]).count() == 4

    def test_slicing_indexing(self):
        Student.objects.delete()
        with BlockSave(Student):
            Student(name='Olavi', surname='Mikkonen').save()
            Student(name='Johan', surname='Hegg').save()
            Student(name='Johan', surname='Soderberg').save()
            Student(name='Ted', surname='Lundstrom').save()
            Student(name='Michael', surname='Amott').save()
            Student(name='Daniel', surname='Erlandsson').save()
            Student(name='Sharlee', surname='D\'Angelo').save()
            Student(name='Alissa', surname='White-Gluz').save()
            Student(name='Jeff', surname='Loomis').save()
        # Check regular slices
        assert Student.objects.count() == 9
        assert Student.objects[2:5].count() == 3
        assert Student.objects[1:5].count() == 4
        assert Student.objects[1:6].count() == 5
        assert Student.objects[0:10].count() == 9
        assert Student.objects[0:11].count() == 9
        assert Student.objects[1:11].count() == 8
        assert Student.objects[1:12].count() == 8
        # Check multi-slicing
        assert Student.objects[1:6][2:4].count() == 2
        assert Student.objects[0:7][2:4].count() == 2
        assert Student.objects[0:7][2:5].count() == 3
        # Check get & indexing
        s1 = Student.objects[3:4].get()
        s2 = Student.objects[3:4][0]
        assert s1 == s2
        s1 = Student.objects[3:9][4:5].get()
        s2 = Student.objects[3:9][4:5][0]
        assert s1 == s2
        # Check slicing with filters
        assert Student.objects.filter(name__startswith='J')[1:3].count() == 2
        assert Student.objects.filter(name__startswith='J')[2:3].get() is not None

    def test_escaping(self):
        Student.objects.delete()
        with BlockSave(Student):
            Student(name='jhon smith', surname='jr.').save()
            Student(name='jhon smith', surname='sr.').save()
        # assert Student.objects.filter(name__contains='on sm').count() == 2
        assert Student.objects.filter(name='jhon smith').count() == 2

    def test_distinct_values_of(self):
        user, new = User.objects.get_or_create(name="Sergio Mena")
        role_lst = []
        with BlockSave(Role):
            for i in range(1, 6, 1):
                role = Role(name="Musician%s" % i, usr=user)
                role.save()
                role_lst.append(role)

        user_dict_1 = Role.objects.filter(name="Musician1").distinct_values_of("usr_id")
        assert sum(user_dict_1.values()) == 1

        user_dict_2 = Role.objects.filter(usr_id=user.key).distinct_values_of("usr_id")
        assert sum(user_dict_2.values()) == 5

        Role.objects.filter(active=True).delete()

        with BlockSave(Role, query_dict={'active': True}):
            for i, r in enumerate(role_lst):
                if i == 3:
                    pass
                else:
                    r.active = True
                    r.save()

        user_dict_3 = Role.objects.filter(active=True).distinct_values_of("usr_id")
        assert sum(user_dict_3.values()) == 4

        new_user = User(name="Valnetin Hegg")
        new_user.blocking_save()
        role_lst[0].usr = new_user
        role_lst[0].blocking_save(query_dict={'usr': new_user})
        user_dict_4 = Role.objects.filter(active=True, usr_id=user.key).distinct_values_of("usr_id")
        assert sum(user_dict_4.values()) == 3

        with BlockDelete(Role):
            for r in role_lst:
                r.delete()
