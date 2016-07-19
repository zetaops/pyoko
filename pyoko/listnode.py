# -*-  coding: utf-8 -*-
"""
This module holds the ListNode implementation of Pyoko Models.

ListNode's are used to model ManyToMany relations and other
list like data types on a Model.
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import six

from .node import Node
from .lib.utils import un_camel, un_camel_id, lazy_property


class ListNode(Node):
    """
    ListNode's are used to store list of field sets.
    Their DB representation look like list of dicts:

    .. code-block:: python

        class Student(Model):
            class Lectures(ListNode):
                name = field.String()
                code = field.String(required=False)

        st = Student()
        st.Lectures(name="Math101", code='M1')
        st.Lectures(name="Math102", code='M2')
        st.clean_value()
        {
            'deleted': False,
            'timestamp': None
            'lectures': [
                {'code': 'M1', 'name': 'Math101'},
                {'code': 'M2', 'name': 'Math102'},
            ]
        }



    Notes:
        - Currently we disregard the ordering of ListNode items.
        - "reverse_name" dose not supported on linked models.

    """

    _TYPE = 'ListNode'

    def __init__(self, **kwargs):
        # self._is_item = False
        # self._from_db = False
        # self.values = []
        # self.node_stack = []
        # self.node_dict = {}
        self.setattrs(
            _is_item=False,
            _from_db=False,
            values=[],
            node_stack=[],
            node_dict={},
        )
        super(ListNode, self).__init__(**kwargs)
        self.setattrs(_data=[])

    @lazy_property
    def objects(self):
        links = self.get_links()
        if links:
            lnk = links[0]
            root_lnk = self._root_node.get_link(field=self.__class__.__name__, startswith=True)
            if root_lnk['reverse'].endswith('_set'):
                remote_name = un_camel_id("%s.%s" % (root_lnk['reverse'], root_lnk['reverse'][:-4]))
            else:
                remote_name = un_camel_id(root_lnk['reverse'])
            return lnk['mdl'].objects.filter(**{remote_name:self._root_node.key})

    def _load_data(self, data, from_db=False):
        """
        Stores the data at self._data, actual object creation done at _generate_instances()

        Args:
            data (list): List of dicts.
            from_db (bool): Default False. Is this data coming from DB or not.
        """
        self._data = data[:]
        self.setattrs(
            values=[],
            node_stack=[],
            node_dict={},
        )
        self._from_db = from_db

    def _generate_instances(self):
        """
        ListNode item generator. Will be used internally by __iter__ and __getitem__

        Yields:
            ListNode items (instances)
        """
        for node in self.node_stack:
            yield node
        while self._data:
            yield self._make_instance(self._data.pop(0))

    def _make_instance(self, node_data):
        """
        Create a ListNode instance from node_data

        Args:
            node_data (dict): Data to create ListNode item.
        Returns:
            ListNode item.
        """
        node_data['from_db'] = self._from_db
        clone = self.__call__(**node_data)
        clone.setattrs(container = self,
                    _is_item = True)
        for name in self._nodes:
            _name = un_camel(name)
            if _name in node_data:  # check for partial data
                getattr(clone, name)._load_data(node_data[_name])
        _key = clone._get_linked_model_key()
        if _key:
            self.node_dict[_key] = clone
        return clone

    def _get_linked_model_key(self):
        """
        Only one linked model can represent a listnode instance,

        Returns:
             The first linked models key if exists otherwise None
        """
        for lnk in self.get_links():
            return getattr(self, lnk['field']).key

    def clean_value(self):
        """
        Populates json serialization ready data.
        This is the method used to serialize and store the object data in to DB

        Returns:
            List of dicts.
        """
        result = []
        for mdl in self:
            result.append(super(ListNode, mdl).clean_value())
        return result

    def __repr__(self):
        """
        This works for two different object:
            - Main ListNode object
            - Items of the ListNode (like instance of a class)
              which created while iterating on main ListNode object

        Returns:
            String representation of object.
        """
        if not self._is_item:
            return [obj for obj in self[:10]].__repr__()
        else:
            try:
                u = six.text_type(self)
            except (UnicodeEncodeError, UnicodeDecodeError):
                u = '[Bad Unicode data]'
            return six.text_type('<%s: %s>' % (self.__class__.__name__, u))

    # def __hash__(self):
    #     if self.HASH_BY:
    #         return hash(getattr(self, self.HASH_BY))

    def add(self, **kwargs):
        """
        Stores node data without creating an instance of it.
        This is more efficient if node instance is not required.

        Args:
            kwargs: attributes of the ListNode
        """
        self._data.append(kwargs)

    def pre_add(self):
        """
        A hook for doing things before adding new listnode item to the stack
        """
        pass

    def __call__(self, **kwargs):
        """
        Stores created instance in node_stack and returns it's reference to callee
        """
        kwargs['_root_node'] = self._root_node
        clone = self.__class__(**kwargs)
        clone.setattrs(_is_item = True)
        clone.pre_add()
        self.node_stack.append(clone)
        _key = clone._get_linked_model_key()
        if _key:
            self.node_dict[_key] = clone
        return clone

    def clear(self):
        """
        Clear outs the list node.

        Raises:
            TypeError: If it's called on a ListNode item (intstead of ListNode's itself)
        """
        if self._is_item:
            raise TypeError("This an item of the parent ListNode")
        self.node_stack = []
        self._data = []

    def __contains__(self, item):
        if self._data:
            return any([d[un_camel_id(item.__class__.__name__)] == item.key for d in self._data])
        else:
            return item.key in self.node_dict

    def __len__(self):
        # FIXME: Partial evolution of ListNode iterator can cause incorrect results
        return len(self._data or self.node_stack)

    def __getitem__(self, index):
        return list(self._generate_instances()).__getitem__(index)

    def __iter__(self):
        return self._generate_instances()

    def __setitem__(self, key, value):
        # This is not useful in current state. Should be refactored or removed.
        if self._is_item:
            raise TypeError("This an item of the parent ListNode")
        self.node_stack[key] = value

    def __delitem__(self, obj, sync=True):
        """
        Allow usage of "del" statement on ListNodes with bracket notation.

        Args:
            obj: ListNode item or relation key.

        Raises:
            TypeError: If it's called on a ListNode item (intstead of ListNode's itself)
        """
        if self._is_item:
            raise TypeError("This an item of the parent ListNode")
        list(self._generate_instances())
        _lnk_key = None
        if isinstance(obj, six.string_types):
            _lnk_key = obj
            _obj = self.node_dict[obj]
        elif not isinstance(obj, self.__class__):
            _lnk_key = obj.key
            _obj = self.node_dict[obj.key]
            del self.node_dict[obj.key]
        else:
            _obj = obj
        self.node_stack.remove(_obj)
        if _lnk_key and sync:
            # this is a "many_to_n" relationship,
            # we should cleanup other side too.
            rel_name = "%s.%s" % (_obj.__class__.__name__,
                                  _obj.get_link()['field'])
            remote_node_name = self._root_node.get_link(field=rel_name)['reverse']
            _lnk_obj = getattr(_obj, _obj.get_link()['field'])
            getattr(_lnk_obj, remote_node_name).__delitem__(self._root_node.key, sync=False)
            # binding relation's save to root objects save
            self._root_node.on_save.append(_lnk_obj.save)

    def remove(self):
        """
        Removes an item from ListNode.

        Raises:
            TypeError: If it's called on container ListNode (intstead of ListNode's item)

        Note:
            Parent object should be explicitly saved.
        """
        if not self._is_item:
            raise TypeError("Should be called on an item, not ListNode's itself.")
        self.container.node_stack.remove(self)
