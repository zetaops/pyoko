# -*-  coding: utf-8 -*-
"""
This module holds the pyoko's Model object
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import six
import time

from pyoko.exceptions import IntegrityError, ObjectDoesNotExist
from .node import Node, FakeContext
from . import fields as field
from .db.queryset import QuerySet
from .lib.utils import un_camel, lazy_property, pprnt, un_camel_id
import weakref

super_context = FakeContext()

# kept for backwards-compatibility
from .modelmeta import model_registry


class Model(Node):
    """
    This is base class for any model object.

    Field instances are used as model attributes to represent values.

    .. code-block:: python

        class Permission(Model):
            name = field.String("Name")
            code = field.String("Code Name")

            def __unicode__(self):
                return "%s %s" % (self.name, self.code)

    Models may have inner classes to represent ManyToMany relations, inner data nodes or lists.

    Notes:
        - "reverse_name" does not supported on links from ListNode's.

    """
    objects = QuerySet
    _TYPE = 'Model'

    _DEFAULT_BASE_FIELDS = {
        'timestamp': field.DateTime(default='now'),
        'updated_at': field.TimeStamp(),
        'deleted_at': field.DateTime(),
        'deleted': field.Boolean(default=False, index=True)
    }
    _SEARCH_INDEX = ''

    def __init__(self, context=None, **kwargs):
        # holds list of banned fields for current context
        # self._unpermitted_fields = []
        # this indicates cell filters applied and we can filter on them
        # self._is_unpermitted_fields_set = False
        # self._context = context
        self.setattrs(
            reverse_link=kwargs.get('reverse_link', False),
            key=kwargs.pop('key', None),
            _unpermitted_fields=[],
            _context=context,
            verbose_name=kwargs.get('verbose_name'),
            null=kwargs.get('null', False),
            unique=kwargs.get('unique'),
            reverse_name=None,
            _pass_perm_checks=kwargs.pop('_pass_perm_checks', False),
            _is_one_to_one=kwargs.pop('one_to_one', False),
            title=kwargs.pop('title', self.__class__.__name__),
            _root_node=self,
            new_back_links={},
            _just_created=None,
            just_created=None,
            on_save=[],
            _exists=None,
        )
        # self.verbose_name = kwargs.get('verbose_name')
        # self.null = kwargs.get('null', False)
        # self.unique = kwargs.get('unique')
        # self.reverse_name = kwargs.get('reverse_name')
        # self._pass_perm_checks = kwargs.pop('_pass_perm_checks', False)
        # self._is_one_to_one = kwargs.pop('one_to_one', False)
        # self.title = kwargs.pop('title', self.__class__.__name__)
        # self._root_node = self
        # self.save_meta_data = None
        # used as a internal storage to wary of circular overwrite of the self.just_created
        # self._just_created = None
        # self._pre_save_hook_called = False
        # self._post_save_hook_called = False
        # self.new_back_links = {}
        self.objects._pass_perm_checks = self._pass_perm_checks
        kwargs['context'] = context
        super(Model, self).__init__(**kwargs)

        self.objects.set_model(model=self)
        self.setattrs(objects=self.row_level_access(self._context, self.objects))
        self._instance_registry.add(weakref.ref(self))
        # self.saved_models = []

    def __str__(self):
        try:
            return self.__unicode__()
        except AttributeError:
            return "%s object" % self.__class__.__name__

    def get_verbose_name(self):
        """
        Returns:
            Verbose name of the model instance
        """
        return self.verbose_name or self.Meta.verbose_name

    def prnt(self):
        """
        Prints DB data representation of the object.
        """
        print("= = = =\n\n%s object key: \033[32m%s\033[0m" % (self.__class__.__name__, self.key))
        pprnt(self._data or self.clean_value())

    def __eq__(self, other):
        """
        Equivalence of two model instance depends on uniformity of their
        self._data and self.key.
        """
        return self._data == other._data and self.key == other.key

    def __ne__(self, other):
        """
        İnequality of two model instance depends on uniformity of their
        self._data and self.key.
        """

        return not self.__eq__(other)

    def __hash__(self):
        # hash is based on self.key if exists or serialization of object's data.
        if self.key:
            return hash(self.key)
        else:
            clean_value = self.clean_value()
            clean_value['timestamp'] = ''
            return hash(str(clean_value))

    def is_in_db(self):
        """
        Deprecated:
            Use "exist" property instead.
        """
        return self.exist

    @property
    def exist(self):
        """
        Used to check if a relation is exist or a model instance is saved to DB or not.

        Returns:
            True if this model instance stored in DB and has a key and False otherwise.
        """
        return bool(self.key)

    def get_choices_for(self, field):
        """
        Get the choices for the given fields.

        Args:
            field (str): Name of field.

        Returns:
            List of tuples. [(name, value),...]
        """
        choices = self._fields[field].choices
        if isinstance(choices, six.string_types):
            return [(d['value'], d['name']) for d in self._choices_manager.get_all(choices)]
        else:
            return choices

    def set_data(self, data, from_db=False):
        """
        Fills the object's fields with given data dict.
        Internally calls the self._load_data() method.

        Args:
            data (dict): Data to fill object's fields.
            from_db (bool): if data coming from db then we will
            use related field type's _load_data method

        Returns:
            Self. Returns objects itself for chainability.
        """
        self._load_data(data, from_db)
        return self

    def __repr__(self):
        if not self.is_in_db():
            return six.text_type(self.__class__)
        else:
            return self.__str__()

    def _apply_cell_filters(self, context):
        """
        Applies the field restrictions based on the
         return value of the context's "has_permission()" method.
         Stores them on self._unpermitted_fields.

        Returns:
            List of unpermitted fields names.
        """
        self.setattrs(_is_unpermitted_fields_set=True)
        for perm, fields in self.Meta.field_permissions.items():
            if not context.has_permission(perm):
                self._unpermitted_fields.extend(fields)
        return self._unpermitted_fields

    def get_unpermitted_fields(self):
        """
        Gives unpermitted fields for current context/user.

        Returns:
            List of unpermitted field names.
        """
        return (self._unpermitted_fields if self._is_unpermitted_fields_set else
                self._apply_cell_filters(self._context))

    @staticmethod
    def row_level_access(context, objects):
        """
        Can be used to implement context-aware implicit filtering.
        You can define your query filters in here to enforce row level access control.

        If defined, will be called at queryset initialization step and
        it's return value used as Model.objects.

        Args:
            context: An object that contain required user attributes and permissions.
            objects (Queryset): QuerySet object.

        Examples:

            .. code-block:: python
                class FooBar(Model):
                return objects.filter(user=context.user)

        Returns:
            Queryset object.
        """
        return objects

    @lazy_property
    def _name(self):
        return un_camel(self.__class__.__name__)

    @lazy_property
    def _name_id(self):
        return "%s_id" % self._name

    def _update_new_linked_model(self, internal, linked_mdl_ins, link):
        """
        Iterates through linked_models of given model instance to match it's
        "reverse" with given link's "field" values.
        """

        # If there is a link between two sides (A and B), if a link from A to B,
        # link should be saved at B but it is not necessary to control again data in A.
        # If internal field is True, data control is not done and passes.
        if not internal:

            for lnk in linked_mdl_ins.get_links():
                mdl = lnk['mdl']
                if not isinstance(self, mdl) or lnk['reverse'] != link['field']:
                    continue
                local_field_name = lnk['field']
                # remote_name = lnk['reverse']
                remote_field_name = un_camel(mdl.__name__)
                if not link['o2o']:
                    if '.' in local_field_name:
                        local_field_name, remote_field_name = local_field_name.split('.')
                    remote_set = getattr(linked_mdl_ins, local_field_name)

                    if remote_set._TYPE == 'ListNode' and self not in remote_set:
                        remote_set(**{remote_field_name: self._root_node})
                        if linked_mdl_ins._exists is False:
                            raise ObjectDoesNotExist(
                                'Linked %s on field %s with key %s doesn\'t exist' % (
                                    linked_mdl_ins.__class__.__name__,
                                    remote_field_name,
                                    linked_mdl_ins.key,
                                ))
                        linked_mdl_ins.save(internal=True)
                else:
                    linked_mdl_ins.setattr(remote_field_name, self._root_node)
                    if linked_mdl_ins._exists is False:
                        raise ObjectDoesNotExist(
                            'Linked object %s on field %s with key %s doesn\'t exist' % (
                                linked_mdl_ins.__class__.__name__,
                                remote_field_name,
                                linked_mdl_ins.key,
                            ))
                    linked_mdl_ins.save(internal=True)

    def _add_back_link(self, linked_mdl, link):
        # creates a new back_link reference
        self.new_back_links["%s_%s_%s" % (linked_mdl.key,
                                          link['field'],
                                          link['o2o'])] = (linked_mdl, link.copy())

    def _handle_changed_fields(self, old_data):
        """
        Looks for changed relation fields between new and old data (before/after save).
        Creates back_link references for updated fields.

        Args:
            old_data: Object's data before save.
        """
        for link in self.get_links(is_set=False):
            fld_id = un_camel_id(link['field'])
            if not old_data or old_data.get(fld_id) != self._data[fld_id]:
                # self is new or linked model changed
                if self._data[fld_id]:  # exists
                    linked_mdl = getattr(self, link['field'])
                    self._add_back_link(linked_mdl, link)
                if old_data.get(fld_id, False) and link['reverse_link']:
                    self.delete_invalid_link(link['mdl'], link['reverse'], old_data[fld_id])

    def _handle_changed_listnode_fields(self, old_data):
        """
        Compares old data's listnode fields and new data's
        listnode fields. If a link is changed, data is
        deleted from old side and appended to new side.

        Args:
            old_data: Object's data before save.
        """

        append_dict = {}
        for link in self.get_links(model_listnode=True, reverse_link=True):

            if old_data:
                l_node_name, field_name = link['field'].split('.')
                l_node_name = un_camel(l_node_name)
                field_name = un_camel_id(field_name)

                if old_data.get(l_node_name,False) and old_data[l_node_name] != self._data[l_node_name]:
                    old = [i[field_name] for i in old_data[l_node_name] if i[field_name] is not None]
                    new = [i[field_name] for i in self._data[l_node_name] if i[field_name] is not None]

                    removed = set(old) - set(new)
                    appended = set(new) - set(old)

                    for appended_key in appended: append_dict[appended_key] = link

                    for removed_key in removed:
                        self.delete_invalid_link(link['mdl'], link['reverse'], removed_key)

        self.add_new_appended_links(append_dict)

    def add_new_appended_links(self,append_dict):
        """
        Adds new back link references.

        Args:
            append_dict(dict): Contains updated objects key
            and link data to create back_link references.
        """
        for appended_key,appended_link in append_dict.items():
            if not any(appended_key in s for s in self.new_back_links.keys()):
                obj = appended_link['mdl'].objects.get(appended_key)
                self._add_back_link(obj, appended_link)

    def delete_invalid_link(self, mdl, reverse, key):
        """
        Removes invalid links after data is updated.

        Args:
            mdl: object's model.
            reverse: reverse set reference.
            key: object's database key.
        """
        removed_obj = mdl.objects.get(key)
        linked_set = getattr(removed_obj, reverse)
        if self in linked_set:
            linked_set.__delitem__(self,sync = False)
            removed_obj.save()

    def _process_relations(self, internal):
        buffer = []
        for k, v in self.new_back_links.copy().items():
            del self.new_back_links[k]
            if v[1]['o2o'] or v[1]['reverse_link']:
                buffer.append(v)
        for v in buffer:
            self._update_new_linked_model(internal, *v)

    def reload(self):
        """
        Reloads current instance from DB store
        """
        self._load_data(self.objects.data().filter(key=self.key)[0][0], True)

    def pre_save(self):
        """
        Called before object save.
        Can be overriden to do things that should be done just before
        object saved to DB.
        """
        pass

    def post_save(self):
        """
        Called after object save.
        Can be overriden to do things that should be done after object
        saved to DB.
        """
        pass

    def pre_delete(self):
        """
        Called before object deletion.
        Can be overriden to do things that should be done
        before object is marked deleted.
        """
        pass

    def post_delete(self):
        """
        Called after object deletion.
        Can be overriden to do things that should be done
        after object is marked deleted.
        """
        pass

    def post_creation(self):
        """
        Called after object's creation (first save).
        Can be overriden to do things that should be done after object
        saved to DB.
        """
        pass

    def pre_creation(self):
        """
        Called before object's creation (first save).
        Can be overriden to do things that should be done before object
        saved to DB.
        """
        pass

    def _handle_uniqueness(self):
        """

        Raises:
            IntegrityError if unique and unique_together checks does not pass
        """

        def _getattr(u):
            try:
                return self._field_values[u]
            except KeyError:
                return getattr(self, u)

        if self._uniques:
            for u in self._uniques:
                val = _getattr(u)
                if val and self.objects.filter(**{u: val}).count():
                    raise IntegrityError("Unique mismatch: %s for %s already exists for value: %s" %
                                         (u, self.__class__.__name__, val))
        if self.Meta.unique_together:
            for uniques in self.Meta.unique_together:
                vals = dict([(u, _getattr(u)) for u in uniques])
                if self.objects.filter(**vals).count():
                    raise IntegrityError(
                        "Unique together mismatch: %s combination already exists for %s"
                        % (vals, self.__class__.__name__))

    def save(self, internal=False, meta=None, index_fields=None):
        """
        Save's object to DB.

        Do not override this method, use pre_save and post_save methods.

        Args:
            internal (bool): True if called within model.
                Used to prevent unneccessary calls to pre_save and
                post_save methods.
            meta (dict): JSON serializable meta data for logging of save operation.
                {'lorem': 'ipsum', 'dolar': 5}
            index_fields (list): Tuple list for indexing keys in riak (with 'bin' or 'int').
                [('lorem','bin'),('dolar','int')]

        Returns:
             Saved model instance.
        """
        for f in self.on_save:
            f(self)
        if not (internal or self._pre_save_hook_called):
            self._pre_save_hook_called = True
            self.pre_save()
        if not self.exist:
            self._handle_uniqueness()
            self.pre_creation()
        old_data = self._data.copy()
        if self.just_created is None:
            self.setattrs(just_created=not self.exist)
        if self._just_created is None:
            self.setattrs(_just_created=self.just_created)
        self.objects.save_model(self, meta_data=meta, index_fields=index_fields)
        self._handle_changed_fields(old_data)
        self._handle_changed_listnode_fields(old_data)
        self._process_relations(internal)
        if not (internal or self._post_save_hook_called):
            self._post_save_hook_called = True
            self.post_save()
            if self._just_created:
                self.setattrs(just_created=self._just_created,
                              _just_created=False)
                self.post_creation()
        return self

    def changed_fields(self):
        """
        Returns:
            list: List of fields names which their values changed.
        """
        current_dict = self.clean_value()
        # `from_db` attr is set False as default, when a `ListNode` is
        # initialized just after above `clean_value` is called. `from_db` flags
        # in 'list node sets' makes differences between clean_data and object._data.

        # Thus, after clean_value, object's data is taken from db again.
        db_data = self.objects.data().filter(key=self.key)[0][0]

        set_current, set_past = set(current_dict.keys()), set(db_data.keys())
        intersect = set_current.intersection(set_past)
        return set(o for o in intersect if db_data[o] != current_dict[o])

    def is_changed(self, field):
        """
        Args:
            field (string):Field name.

        Returns:
            bool: True if given fields value is changed.
        """
        return field in self.changed_fields()

    def blocking_save(self, query_dict=None):
        """
        Saves object to DB. Waits till the backend properly indexes the new object.

        Args:
            query_dict(dict) : contains keys - values of  the model fields

        Returns:
            Model instance.
        """
        query_dict = query_dict or {}
        for query in query_dict:
            self.setattr(query, query_dict[query])

        self.save()
        while not self.objects.filter(key=self.key, **query_dict).count():
            time.sleep(0.3)
        return self

    def blocking_delete(self):
        """
        Deletes and waits till the backend properly update indexes for just deleted object.
        """
        self.delete()
        while self.objects.filter(key=self.key).count():
            time.sleep(0.3)

    def _traverse_relations(self):
        for lnk in self.get_links(link_source=False):
            yield (lnk,
                   list(
                       lnk['mdl'].objects.filter(**{'%s_id' % un_camel(lnk['reverse']): self.key})))

    def _delete_relations(self, dry=False):
        for lnk, rels in self._traverse_relations():
            for rel in rels:
                key = lnk['reverse'].split('.')[0]
                lnkd_model = getattr(rel, key)
                if lnkd_model._TYPE == 'ListNode':
                    del lnkd_model[self]
                elif lnkd_model._TYPE == 'Model':
                    rel.setattr(key, None)
                # binding actual relation's save to our save
                self.on_save.append(lambda self: rel.save(internal=True))

        return [], []

    def delete(self, dry=False, meta=None, index_fields=None):
        """
        Sets the objects "deleted" field to True and,
        current time to "deleted_at" fields then saves it to DB.


        Args:
            dry (bool): False. Do not execute the actual deletion.
            Just list what will be deleted as a result of relations.
            meta (dict): JSON serializable meta data for logging of save operation.
                {'lorem': 'ipsum', 'dolar': 5}
            index_fields (list): Tuple list for secondary indexing keys in riak (with 'bin' or 'int').
                [('lorem','bin'),('dolar','int')]
        Returns:
            Tuple. (results [], errors [])
        """
        from datetime import datetime
        # TODO: Make sure this works safely (like a sql transaction)
        if not dry:
            self.pre_delete()
        results, errors = self._delete_relations(dry)
        if not (dry or errors):
            self.deleted = True
            self.deleted_at = datetime.now()
            self.save(internal=True, meta=meta, index_fields=index_fields)
            self.post_delete()
        return results, errors


class LinkProxy(object):
    """
    Proxy object for "self" referencing model relations
    Example:

        .. code-block:: python

            class Unit(Model):
                name = field.String("Name")
                parent = LinkProxy('Unit', verbose_name='Upper unit', reverse_name='sub_units')

    """
    _TYPE = 'Link'

    def __init__(self, link_to,
                 one_to_one=False,
                 verbose_name=None,
                 reverse_name=None,
                 reverse_link=False,
                 null=False,
                 unique=False):
        self.link_to = link_to
        self.unique = unique
        self.null = null
        self.one_to_one = one_to_one
        self.verbose_name = verbose_name
        self.reverse_name = None
        self.reverse_link = reverse_link
