# -*-  coding: utf-8 -*-
"""
riak client configuration
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

import riak
import json
import six
from pyoko.conf import settings
from riak.client.multi import MultiGetPool
from riak.client.multi import Empty
from redis import Redis

redis_host, redis_port = settings.REDIS_SERVER.split(':')
cache = Redis(redis_host, redis_port)

client = riak.RiakClient(protocol=settings.RIAK_PROTOCOL,
                         host=settings.RIAK_SERVER,
                         http_port=settings.RIAK_PORT)

riak.disable_list_exceptions = True

class PyokoMG(MultiGetPool):
    def _worker_method(self):
        """
        The body of the multi-get worker. Loops until
        :meth:`_should_quit` returns ``True``, taking tasks off the
        input queue, fetching the object, and putting them on the
        output queue.
        """
        while not self._should_quit():
            try:
                task = self._inq.get(block=True, timeout=0.25)
            except TypeError:
                if self._should_quit():
                    break
                else:
                    raise
            except Empty:
                continue

            try:
                obj_data = cache.get(task.key)
                if not obj_data:
                    btype = task.client.bucket_type(task.bucket_type)
                    obj = btype.bucket(task.bucket).get(task.key, **task.options)
                    cache.set(task.key, json.dumps(obj.data))
                    task.outq.put((obj.key,obj.data))
                else:
                    task.outq.put((task.key,json.loads(obj_data)))


                    # if settings.ENABLE_CACHING:
                    #     obj_data = cache.get(task.key)
                    #     if not obj_data:
                    #         btype = task.client.bucket_type(task.bucket_type)
                    #         obj = btype.bucket(task.bucket).get(task.key, **task.options)
                    #         obj_data = obj.data.decode() if six.PY3 else obj.data
                    #         cache.set(task.key, json.dumps(obj_data))
                    #         task.outq.put((obj_data, obj.key))
                    #     else:
                    #         if six.PY3:
                    #             obj_data = obj_data.decode()
                    #         task.outq.put((obj_data, task.key))
                    # else:
                    #     btype = task.client.bucket_type(task.bucket_type)
                    #     obj = btype.bucket(task.bucket).get(task.key, **task.options)
                    #     obj_data = obj.data.decode() if six.PY3 else obj.data
                    #     task.outq.put((obj_data, obj.key))

            except KeyboardInterrupt:
                raise
            except Exception as err:
                errdata = (task.bucket_type, task.bucket, task.key, err)
                task.outq.put(errdata)
            finally:
                self._inq.task_done()


log_bucket = client.bucket_type(
    settings.VERSION_LOG_BUCKET_TYPE).bucket(settings.ACTIVITY_LOGGING_BUCKET)

version_bucket = client.bucket_type(
    settings.VERSION_LOG_BUCKET_TYPE).bucket(settings.VERSION_BUCKET)