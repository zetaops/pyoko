# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
# from ulakbus.models.personel import Personel
from pyoko.db.connection import log_bucket, version_bucket
from .models import AbstractRole



class TestCase():
    """
    when save() and delete() operations are executed without meta parameter
    just version_log should execute otherwise with meta parameter both of them
    should execute.

    """
    # Random sample meta_data is created.
    meta_data = {'lorem': 'ipsum', 'dolar': 5}
    index_fields = [('lorem','bin'),('dolar','int')]
    # Instances are created from Abstract model.
    abs_role = AbstractRole()
    another_abs_role = AbstractRole()
    log_bucket_count = None
    version_bucket_count = None
    last_version_keys = None
    last_log_keys = None

    def test_save_delete_without_meta_data(self):
        # Log, version keys and counts are updated.
        update_log_version_keys(self)
        # Abstract role's name is defined.
        self.abs_role.name = 'example_name'
        # Object is saved without meta data.
        self.abs_role.save()
        # Log bucket should remain same.
        # Version bucket count should increase one.
        common_controls_without_meta_data(self)
        # Log, version keys and counts are updated.
        update_log_version_keys(self)
        # Object is deleted without meta data.
        self.abs_role.delete()
        # Log bucket should remain same.
        # Version bucket count should increase one.
        common_controls_without_meta_data(self)

    def test_save_with_meta_data(self):
        # Other abstract role's name is changed.
        self.another_abs_role.name = 'sample_name'
        # Log, version keys and counts are updated.
        update_log_version_keys(self)
        # Object is saved with meta data.
        self.another_abs_role.save(meta=self.meta_data, index_fields=self.index_fields)
        # Log bucket count should increase one.
        # Version bucket count should increase one.
        deleted_and_name_control = common_controls_with_meta_data(self)
        # In version bucket, name key should be defined name.
        # Deleted key should be False.
        assert deleted_and_name_control == ('sample_name',False)


    def test_delete_with_meta_data(self):
        # Log, version keys and counts are updated.
        update_log_version_keys(self)
        # Object is deleted with meta_data.
        self.another_abs_role.delete(meta = self.meta_data,index_fields=self.index_fields)
        # Log bucket count should increase one.
        # Version bucket count should increase one.
        deleted_and_name_control = common_controls_with_meta_data(self)
        # In version bucket, deleted key should be True.
        # Name key should be defined name.
        assert deleted_and_name_control == ('sample_name',True)

def common_controls_without_meta_data(self):
    # Controlling log_bucket remain same.
    assert len(log_bucket.get_keys()) == self.log_bucket_count
    # Version bucket record count should be one more than old count.
    assert len(version_bucket.get_keys()) == self.version_bucket_count + 1

def common_controls_with_meta_data(self):
    # New log bucket record count should be one more than old count.
    assert len(log_bucket.get_keys()) == self.log_bucket_count + 1
    # New version bucket record count should be one more than old count.
    assert len(version_bucket.get_keys()) == self.version_bucket_count + 1
    # New log key is found from difference before and after bucket_keys.
    new_log_key = list(set(log_bucket.get_keys()) - set(self.last_log_keys))
    # New version key is found from difference before and after bucket_keys.
    new_version_key = list(set(version_bucket.get_keys()) - set(self.last_version_keys))
    # Log, version keys and counts are updated.
    update_log_version_keys(self)
    # There should be one different key before and after log records.
    assert len(new_log_key) == 1
    # There should be one different key before and after version records.
    assert len(new_version_key) == 1
    # New log data is taken.
    log_data = log_bucket.get(new_log_key[0]).data
    # New log indexes are taken.
    indexes = log_bucket.get(new_log_key[0]).indexes
    # Indexes are controlled.
    assert ('lorem_bin','ipsum') in indexes
    assert ('dolar_int', 5) in indexes
    # New version key and log_bucket's record's version key should be same.
    assert log_data['version_key'] == new_version_key[0]
    # Changes are controlled.
    assert log_data['lorem'] == 'ipsum'
    assert log_data['dolar'] == 5
    # New version data is taken.
    version_data = version_bucket.get(new_version_key[0]).data
    # Model value should be 'abstract_role'.
    assert version_data['model'] == 'abstract_role'
    # Riak key is controlled.
    assert version_data['key'] == self.another_abs_role.key

    return version_data['data']['name'],version_data['data']['deleted']

def update_log_version_keys(self):
    # Record count before save and delete operation in log bucket.
    self.log_bucket_count = len(log_bucket.get_keys())
    # Record count before save and delete operation in version bucket.
    self.version_bucket_count = len(version_bucket.get_keys())
    # Keys list in version bucket.
    self.last_version_keys = version_bucket.get_keys()
    # Keys list in log bucket.
    self.last_log_keys = log_bucket.get_keys()



