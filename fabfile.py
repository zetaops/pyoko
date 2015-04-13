# -*-  coding: utf-8 -*-
"""
run test_methods.py on remote
'fab test' for CPython env
'fab test:pypy' for PyPy
"""
# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from __future__ import with_statement
import sys
from fabric.api import env, run, cd, prefix
from fabric.contrib.project import rsync_project
from contextlib import contextmanager as _contextmanager

# env.hosts = ['servername']
# env.keyfile = ['$HOME/.ssh/deploy_rsa']
env.user = 'kunthar'
env.hosts = ['62.210.245.199']
env.port = '99'

if 'pypy' in ''.join(sys.argv):
    env.directory = '/home/kunthar/test-riak-pypy'
    env.activate = 'source /home/kunthar/.virtualenvs/pypy/bin/activate'
else:
    env.directory = '/home/kunthar/test-riak'
    env.activate = 'source /home/kunthar/.virtualenvs/test-riak/bin/activate'


@_contextmanager
def virtualenv():
    with cd(env.directory):
        with prefix(env.activate):
            yield


def sync(foo=None):
    """
    syncs the files with test machine (to home dir. by default)
    """
    rsync_project(env.directory, local_dir=".", default_opts='-pthrz',
                  exclude="*.log local_settings.py *.json fabfile *.pyc *~ .idea .git *.png".split(' '),
                  )


def _test():
    with virtualenv():
        run("python data_generator.py")


def test(foo=None):
    sync()
    _test()
