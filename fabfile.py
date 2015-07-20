# -*-  coding: utf-8 -*-
from __future__ import with_statement
# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

from fabric.api import env, run, cd, prefix
from fabric.context_managers import shell_env
from fabric.contrib.project import rsync_project, os
from contextlib import contextmanager as _contextmanager


# set this environmental variables
ENV_VARS = [
    # variable name, default value, internal name),
    ('TEST_SERVER_ADDR', '', 'host_string'),
    ('INTERNAL_RIAK_ADDR', '', 'riak_addr'),
    # defaults may work for the followings
    ('PROJECT_NAME', 'pyoko', 'project_name'),
    ('TEST_SERVER_USER', '', 'user'),
    ('TEST_SERVER_PORT', '22', 'port'),
    ('PROJECT_DIR', '~/{project_name}', 'directory'),
    ('VENV_ACTIVATE_PATH', '~/.virtualenvs/{project_name}/bin/activate', 'activate'),
]

for env_var, def_val, int_name in ENV_VARS:
    env[int_name] = os.environ.get(env_var, def_val).format(**env)

REMOTE_ENV_VARS = {
    'PYOKO_SETTINGS': 'tests.settings',
    'RIAK_SERVER': env.riak_addr
}


@_contextmanager
def _virtualenv():
    with cd(env.directory + "tests"):
        with prefix(env.activate):
            with shell_env(**REMOTE_ENV_VARS):
                yield


def copy():
    """
    copy the files to the server (test machine)
    """
    rsync_project(env.directory, local_dir=".", default_opts='-pthrz',
                  exclude="*.log __exclude local_settings.* __pycache__ *.pyc *~ .idea .git".split(
                      ' '))


def test(keyword='', verbose=True, sync=True):
    """
    sync project then run tests on remote machine
    :param keyword: limit tests by name. prefix with "not" for exclusion
    :param verbose: be verbose (-vv)
    :param sync: Copy files to remote before running tests
    """
    if sync:
        copy()
    cmd = ['py.test']
    if keyword:
        cmd.append("-k %s" % keyword)
    if verbose:
        cmd.append("-vv")
    with _virtualenv():
        run(' '.join(cmd))


def update():
    with _virtualenv():
        run("python manage.py update_schema --bucket all")


