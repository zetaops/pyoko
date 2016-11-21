# -*-  coding: utf-8 -*-
"""
this module contains a base class for other db access classes
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from collections import defaultdict
import copy
from enum import Enum
from .adapter.db_riak import Adapter
from pyoko.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
import sys

ReturnType = Enum('ReturnType', 'Object Model')

sys.PYOKO_STAT_COUNTER = {
    "save": 0,
    "update": 0,
    "read": 0,
    "count": 0,
    "search": 0,
}
sys.PYOKO_LOGS = defaultdict(list)


# noinspection PyTypeChecker
class QuerySet(object):
    """
    QuerySet is a lazy data access layer for Riak.
    """

    def __init__(self, **conf):
        self._current_context = None
        # pass permission checks to genareted model instances
        self._pass_perm_checks = False
        self._cfg = {'row_size': 1000,
                     'rtype': ReturnType.Model}
        self._cfg.update(conf)
        self._model = None
        self.index_name = ''
        self.is_clone = False
        if 'model' in conf:
            self.set_model(model=conf['model'])
        elif 'model_class' in conf:
            self.set_model(model_class=conf['model_class'])
        # Keeps track of previous slice to allow indexing into a slice
        self._start = None
        self._rows = None

    # ######## Development Methods  #########

    def set_model(self, model=None, model_class=None):
        """

        Args:
            model: Model name
            model_class: Model class
        """
        if model:
            self._model = model
            self._model_class = model.__class__
            self._current_context = self._model._context
            self._cfg['_current_context'] = self._model._context
        if model_class:
            self._model = self._model or None
            self._model_class = model_class
            self._current_context = self._current_context or None
        self._cfg['_model_class'] = self._model_class
        # self._cfg['_objects'] = self.__class__
        self.adapter = Adapter(**self._cfg)

    def distinct_values_of(self, field):
        """
        Args:
            field: field name

        Returns:
            Distinct values of given field.
        """
        return self.adapter.distinct_values_of(field)

    def __iter__(self):
        clone = copy.deepcopy(self)
        for data, key in clone.adapter:
            yield (
                clone._make_model(data, key) if self._cfg['rtype'] == ReturnType.Model else (data, key))

    def __len__(self):
        return copy.deepcopy(self).adapter.count()

    def __getitem__(self, index):
        clone = copy.deepcopy(self)
        if isinstance(index, int):
            # Adjust the index if a slice was defined previously
            adjusted_index = index + (self._start or 0)
            clone.adapter.set_params(rows=1, start=adjusted_index)
            data, key = clone.adapter.get_one()
            return (clone._make_model(data, key)
                    if clone._cfg['rtype'] == ReturnType.Model
                    else (data, key))
        elif isinstance(index, slice):
            if index.start is not None:
                start = int(index.start)
            else:
                start = 0
            if index.stop is not None:
                stop = int(index.stop)
            else:
                stop = None
            if start >= 0 and stop:
                # Adjust the start and rows if a slice was defined previously
                rows = stop - start
                start += self._start or 0
                # Save the slice limits to the sliced queryset, so that further queries on the slice work correctly
                clone._start = start
                clone._rows = rows
                clone.adapter.set_params(rows=rows, start=start)
                return clone
            else:
                raise TypeError("unlimited slicing not supported")
        else:
            raise TypeError("index must be int or slice")

    def __deepcopy__(self, memo=None):
        """
        A deep copy method that doesn't populate caches
        and shares Riak client and bucket
        """
        obj = self.__class__(**self._cfg)
        for k, v in self.__dict__.items():
            if k.endswith(('current_context', 'model', 'model_class')):
                obj.__dict__[k] = v
            elif k == '_cfg':
                obj._cfg = v.copy()
            else:
                if k == '_cfg': print("CFG %s" % v.keys())
                obj.__dict__[k] = copy.deepcopy(v, memo)
        obj.is_clone = True
        return obj

    def save_model(self, model, meta_data=None, index_fields=None):
        """
        saves the model instance to riak
        Args:
            meta (dict): JSON serializable meta data for logging of save operation.
                {'lorem': 'ipsum', 'dolar': 5}
            index_fields (list): Tuple list for secondary indexing keys in riak (with 'bin' or 'int').
                [('lorem','bin'),('dolar','int')]
        :return:
        """
        # if model:
        #     self._model = model
        return self.adapter.save_model(model, meta_data, index_fields)

    def _get(self):
        """
        executes solr query if needed then returns first object according to
        selected ReturnType (defaults to Model)
        :return: pyoko.Model or riak.Object or solr document
        """
        data, key = self.adapter.get_one()
        if self._cfg['rtype'] == ReturnType.Model:
            return self._make_model(data, key)
        else:
            return data

    def _make_model(self, data, key=None):
        """
        Creates a model instance with the given data.

        Args:
            data: Model data returned from DB.
            key: Object key
        Returns:
            pyoko.Model object.
        """
        if data['deleted'] and not self.adapter.want_deleted:
            raise ObjectDoesNotExist('Deleted object returned')
        model = self._model_class(self._current_context,
                                  _pass_perm_checks=self._pass_perm_checks)
        model.setattr('key', key if key else data.get('key'))
        return model.set_data(data, from_db=True)

    def __repr__(self):
        if not self.is_clone:
            return "QuerySet for %s" % self._model_class
        try:
            c = []
            for obj in self:
                c.append(obj.__repr__())
                if len(c) == 10:
                    break
            return c.__repr__()
        except AssertionError as e:
            return e.msg
        except TypeError:
            raise

    def filter(self, **filters):
        """
        Applies given query filters.

        Args:
            **filters: Query filters as keyword arguments.

        Returns:
            Self. Queryset object.

        Examples:
            >>> Person.objects.filter(name='John') # same as .filter(name__exact='John')
            >>> Person.objects.filter(age__gte=16, name__startswith='jo')
            >>> # Assume u1 and u2 as related model instances.
            >>> Person.objects.filter(work_unit__in=[u1, u2], name__startswith='jo')
        """
        clone = copy.deepcopy(self)
        clone.adapter.add_query(filters.items())
        return clone

    def exclude(self, **filters):
        """
        Applies query filters for excluding matching records from result set.

        Args:
            **filters: Query filters as keyword arguments.

        Returns:
            Self. Queryset object.

        Examples:
            >>> Person.objects.exclude(age=None)
            >>> Person.objects.filter(name__startswith='jo').exclude(age__lte=16)
        """
        exclude = {'-%s' % key: value for key, value in filters.items()}
        return self.filter(**exclude)

    def get_or_create(self, defaults=None, **kwargs):
        """
        Looks up an object with the given kwargs, creating a new one if necessary.

        Args:
            defaults (dict): Used when we create a new object. Must map to fields
                of the model.
            \*\*kwargs: Used both for filtering and new object creation.

        Returns:
            A tuple of (object, created), where created is a boolean variable
            specifies whether the object was newly created or not.

        Example:
            In the following example, *code* and *name* fields are used to query the DB.

            .. code-block:: python

                obj, is_new = Permission.objects.get_or_create({'description': desc},
                                                                code=code, name=name)

            {description: desc} dict is just for new creations. If we can't find any
            records by filtering on *code* and *name*, then we create a new object by
            using all of the inputs.


        """
        existing = list(self.filter(**kwargs))
        count = len(existing)
        try:
            if count > 1:
                raise MultipleObjectsReturned(
                    "%s objects returned for %s" % (count,
                                                    self._model_class.__name__))
            if existing[0].deleted:
                raise ObjectDoesNotExist('Sync Issue, deleted object returned!')
            return existing[0], False
        except (ObjectDoesNotExist, IndexError):
            pass

        data = defaults or {}
        data.update(kwargs)
        return self._model_class(**data).save(), True

    def update(self, **kwargs):
        """
        Updates the matching objects for specified fields.

        Note:
            Post/pre save hooks and signals will NOT triggered.

            Unlike RDBMS systems, this method makes individual save calls
            to backend DB store. So this is exists as more of a comfortable
            utility method and not a performance enhancement.

        Keyword Args:
            \*\*kwargs: Fields with their corresponding values to be updated.

        Returns:
            Int. Number of updated objects.

        Example:
            .. code-block:: python

                Entry.objects.filter(pub_date__lte=2014).update(comments_on=False)
        """
        do_simple_update = kwargs.get('simple_update', True)
        no_of_updates = 0
        for model in self:
            no_of_updates += 1
            model._load_data(kwargs)
            model.save(internal=True)
        return no_of_updates

    def get(self, key=None, **kwargs):
        """
        Ensures that only one result is returned from DB and raises an exception otherwise.
        Can work in 3 different way.

            - If no argument is given, only does "ensuring about one and only object" job.
            - If key given as only argument, retrieves the object from DB.
            - if query filters given, implicitly calls filter() method.

        Raises:
            MultipleObjectsReturned: If there is more than one (1) record is returned.
        """
        clone = copy.deepcopy(self)
        # If we are in a slice, adjust the start and rows
        if self._start:
            clone.adapter.set_params(start=self._start)
        if self._rows:
            clone.adapter.set_params(rows=self._rows)
        if key:
            data, key = clone.adapter.get(key)
        elif kwargs:
            data, key = clone.filter(**kwargs).adapter.get()
        else:
            data, key = clone.adapter.get()
        if clone._cfg['rtype'] == ReturnType.Object:
            return data, key
        return self._make_model(data, key)

    def delete(self):
        """
        Deletes all objects that matches to the queryset.

        Note:
            Unlike RDBMS systems, this method makes individual save calls
            to backend DB store. So this is exists as more of a comfortable
            utility method and not a performance enhancement.

        Returns:
            List of deleted objects or None if *confirm* not set.

        Example:
            >>> Person.objects.filter(age__gte=16, name__startswith='jo').delete()

        """
        clone = copy.deepcopy(self)
        # clone.adapter.want_deleted = True
        return [item.delete() and item for item in clone]

    def values_list(self, *args, **kwargs):
        """
        Returns list of values for given fields.
        Since this will implicitly use data() method,
        it's more efficient than simply looping through model instances.


        Args:
            flatten (bool): True. Flatten if there is only one field name given.
             Returns ['one','two', 'three'] instead of
             [['one'], ['two'], ['three]]
            \*args: List of fields to be retured as list.

        Returns:
            List of deleted objects or None if *confirm* not set.

        Example:
            >>> Person.objects.filter(age__gte=16).values_list('name', 'lastname')

        """
        results = []
        for data, key in self.data():
            results.append([data[val] if val != 'key' else key for val in args])
        return results if len(args) > 1 or not kwargs.get('flatten', True) else [
            i[0] for i in results]

    def values(self, *args):
        """
        Returns list of dicts (field names as keys) for given fields.

        Args:
            \*args: List of fields to be returned as dict.

        Returns:
            list of dicts for given fields.

        Example:
            >>> Person.objects.filter(age__gte=16, name__startswith='jo').values('name', 'lastname')

        """
        return [dict(zip(args, values_list))
                for values_list in self.values_list(flatten=False, *args)]

    def dump(self):
        """
        Dump raw JSON output of matching queryset objects.

        Returns:
            List of dicts.

        """
        results = []
        for data in self.data():
            results.append(data)
        return results

    def or_filter(self, **filters):
        """
        Works like "filter" but joins given filters with OR operator.

        Args:
            **filters: Query filters as keyword arguments.

        Returns:
            Self. Queryset object.

        Example:
            >>> Person.objects.or_filter(age__gte=16, name__startswith='jo')

        """
        clone = copy.deepcopy(self)
        clone.adapter.add_query([("OR_QRY", filters)])
        return clone

    def OR(self):
        """
        Switches default query joiner from " AND " to " OR "

        Returns:
            Self. Queryset object.
        """
        clone = copy.deepcopy(self)
        clone.adapter._QUERY_GLUE = ' OR '
        return clone

    def search_on(self, *fields, **query):
        """
        Search for query on given fields.

        Query modifier can be one of these:
            * exact
            * contains
            * startswith
            * endswith
            * range
            * lte
            * gte

        Args:
            \*fields (str): Field list to be searched on
            \*\*query:  Search query. While it's implemented as \*\*kwargs
             we only support one (first) keyword argument.

        Returns:
            Self. Queryset object.

        Examples:
            >>> Person.objects.search_on('name', 'surname', contains='john')
            >>> Person.objects.search_on('name', 'surname', startswith='jo')
        """
        clone = copy.deepcopy(self)
        clone.adapter.search_on(*fields, **query)
        return clone

    def count(self):
        """
        counts by executing solr query with rows=0 parameter
        :return:  number of objects matches to the query
        :rtype: int
        """
        return copy.deepcopy(self).adapter.count()

    def _clear(self):
        """
        Removes all data from model.
        Should be used only for development purposes
        """
        return self.adapter._clear()

    def order_by(self, *args):
        """
        Applies query ordering.

        Args:
            **args: Order by fields names.
            Defaults to ascending, prepend with hypen (-) for desecending ordering.

        Returns:
            Self. Queryset object.

        Examples:
            >>> Person.objects.order_by('-name', 'join_date')
        """
        clone = copy.deepcopy(self)
        clone.adapter.order_by(*args)
        return clone

    def set_params(self, **params):
        """
        add/update solr query parameters
        """
        clone = copy.deepcopy(self)
        clone.adapter.set_params(**params)
        return clone

    def data(self):
        """
        return (data_dict, key) tuple instead of models instances
        """
        clone = copy.deepcopy(self)
        clone._cfg['rtype'] = ReturnType.Object
        return clone

    def raw(self, query):
        """
        make a raw query

        Args:
        query (str): solr query
        \*\*params: solr parameters
        """
        clone = copy.deepcopy(self)
        clone.adapter._pre_compiled_query = query
        clone.adapter.compiled_query = query
        return clone
