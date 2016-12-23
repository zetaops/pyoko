#!/usr/bin/env python
from distutils.core import setup

from setuptools import find_packages

setup(
    name='Pyoko',
    version='0.9.2',
    description='Pyoko is a Django-esque ORM for Riak KV',
    author='Zetaops AS',
    license='GPL v3',
    requires=['enum34', 'six', 'riak', 'lazy_object_proxy'],
    install_requires=['enum34', 'six', 'riak', 'lazy_object_proxy'],
    author_email='info@zetaops.io',
    url='https://github.com/zetaops/pyoko',
    packages=find_packages(exclude=['tests', 'tests.*']),
    package_data={
        'pyoko': ['db/*.xml'],
    },
    keywords=['riak', 'orm', 'database', 'nosql'],
    # download_url='https://github.com/zetaops/pyoko/archive/0.6.2.tar.gz'
)
