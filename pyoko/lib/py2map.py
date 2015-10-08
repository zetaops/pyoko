# -*-  coding: utf-8 -*-
"""
tools to convert Python dicts to / from riak Maps
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
# from riak.datatypes import Map


# class Dictomap(object):
#     """
#     Dictomap converts a given Python dict into riak Map.
#     Accepts str, unicode, numbers, lists and other dicts as values
#     Since Riak Sets does not support anything other than Register as a value,
#     we are flattening and enumerating "list of dicts".
#     eg:
#     d = {'lst':[{'a':1},{'b':2},{'c':3}]}
#     becomes:
#     {('l__lst.0', 'map'): {('a', 'register'): '1'},
#     ('l__lst.1', 'map'): {('b', 'register'): '2'},
#     ('l__lst.2', 'map'): {('c', 'register'): '3'}}
#     """
#     def __init__(self, bucket, dct, key=None):
#         self.map = Map(bucket, key)
#         self.traverse(dct, self.map)
#         # self.map.store()
#
#
#     def traverse(self, dct, mp):
#         for k,v in dct.items():
#             if isinstance(v, dict):
#                 self.traverse(v, mp.maps[str(k)])
#             elif isinstance(v, unicode):
#                 mp.registers[str(k)].assign(v.encode('utf8'))
#             elif isinstance(v, (int, float, str)):
#                 mp.registers[str(k)].assign(str(v))
#             elif isinstance(v, bool):
#                 mp.flags[k].enable() if v else mp.flags[k].disable()
#             elif isinstance(v, list):
#                 for itm in v:
#                     if isinstance(itm, (str, unicode)):
#                         mp.sets[k].add(itm)
#                     elif isinstance(itm, dict):
#                         self.traverse(itm, mp.maps[str('l__%s.%s' % (k, v.index(itm)))])


