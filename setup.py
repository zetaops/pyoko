#!/usr/bin/env python
from distutils.core import setup

from setuptools import find_packages

setup(
    name='Pyoko',
    version='0.1',
    description='Pyoko is a Django-esque ORM for Riak KV',
    author='Zetaops ',
    requires=['enum34', 'six', 'riak', 'lazy_object_proxy'],
    author_email='info@zetaops.io',
    url='https://github.com/zetaops/pyoko',
    packages=find_packages(exclude=['tests', 'tests.*']),
)
