# -*-  coding: utf-8 -*-
#
# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
#
"""
~~~~~~~~~~~~~~
Pyoko Data API
~~~~~~~~~~~~~~

**Version 0.1**

`Pyoko Data API` is REST and AMQP data access API built on
`Pyoko ORM` queryset specifications and Tornado webserver
with `oauth`.

It listens on two endpoint, one is a tcp port for http and
second isan AMQP queue which is bound to an exchange which
gets messages from clients.


Operations
^^^^^^^^^^
- get
- filter
- search
- count
- create
- get or create
- update
- delete

Query Modifiers
^^^^^^^^^^^^^^^
- order by
-

Comparison Operators
^^^^^^^^^^^^^^^^^^^^
- eq (equal)
- gt (greater than)
- gte (greater than or equal)
- lt (less than)
- lte (less than or equal )
- range (between given values)
- in (one of the following items, a shortcut for OR)
- endswith
- startswith

Special Fields
^^^^^^^^^^^^^^
The fields listed below are automatically created with pyoko
model definition and all response have these ones by default:

- `timestamp` keeps creation of record
- `updated_at` keeps last update of record
- `deleted` keeps if the record was deleted or not


Query Definitions
^^^^^^^^^^^^^^^^^
- It is defined inside `q` key as a list::

    "q":[filtering criteria here.. ]

- A key value json object means `eq`::

    "q":[ {"name": "Ali"} ] # name is Ali

- A key value json object with one of the `comparison operators`
documented above corresponds its lexical or abbreviation meaning::

    "q":[ {"name__in": ["Ali", "Ayse"]} ] # name is one of the following, "Ali" or "Ayse"
    "q":[ {"name__startswith": "A"} ] # name starts with "A"

- Multiple key value json object means that all of pairs is conjoined with "AND"::

    "q":[ {"name": "Ali", "age__gte":24]} ] # name is "Ali" and age is greater than or equal 24.

- Multiple objects means that all objects which are conjoined with "OR"::

    "q":[
          {"name": "Ali"]},
          {"age__lte": 24,]},
        ] # Matches persons whose name is "Ali" OR persons whose age is lower than 24.

GET
^^^

Request:
++++++++
Simply specify `model` name and use `key` keyword to get::

    {
     "model": "Student",
     "q": [
            {"key": "W3ED5602LpgET5"},
          ],
     "fields": ["name", "is_active"],
     "auth": {
               "client_secret": "some_screet",
               "auth_token": "token"
               "callback_id": "e67dec5e-1863-11e7-93ae-92361f002671"
             }
    }


Response:
+++++++++
A successful get produce response below::

    {
     "data": {"name": "Ali", "is_active": true},
     "callback_id": "e67dec5e-1863-11e7-93ae-92361f002671"
    }

It contains only `data` and request's `callback_id`. And 200 status
code is sent for HTTP. `data` has only one object.


FILTER
^^^^^^

Request:
++++++++
Simply specify `model` name and filter criteria::

    {
     "model": "Student",
     "q": [
            {"name": "Ali", "age_gt": 24},
          ],
     "fields": ["name", "department", "is_active"],
     "auth": {
               "client_secret": "some_screet",
               "auth_token": "token"
               "callback_id": "e67dec5e-1863-11e7-93ae-92361f002671"
             }
    }

Response:
+++++++++
A successful get produce response below::

    {
     "data": [
               {"name": "Ali", "department": "Math", "is_active": true},
               {"name": "Ali", "department": "Physic", "is_active": false},
               {"name": "Ali", "department": "Computer Science", "is_active": false},
               {"name": "Ali", "department": "History", "is_active": true}
             ]
     "callback_id": "e67dec5e-1863-11e7-93ae-92361f002671"
    }

It contains `data` multiple object list and request's `callback_id`. And 200 status code is sent for HTTP.



"""

from pyoko.db.queryset import QuerySet
from pyoko.modelmeta import model_registry

query_operators = [
    'eq',
    'gt',
    'gte',
    'lt',
    'lte',
    'range',
    'in',
    'endswith',
    'startswith',
]


class PyokoDataAPIError(Exception):
    """
    Pyoko Error
    """
    status_code = 0
    message = ""

    def __init__(self, message_detail=""):
        super(PyokoDataAPIError, self).__init__()
        self.message += "\n \n Details: {}".format(message_detail)


class PyokoUnauthorized(PyokoDataAPIError):
    """
    Unauthorized. If client's credential is not valid. The following
    message is sent accompanied by 401 status code header for HTTP::

        {
         "error": "Unauthorized",
         "data": "Client's credentials are not valid."
         "callback_id": "e67dec5e-1863-11e7-93ae-92361f002671"
        }


    """
    status_code = 401
    message = "Client's credentials are not valid."


class PyokoForbidden(PyokoDataAPIError):
    """
    Unauthorized. If client's credential is not valid. The following
    message is sent accompanied by 401 status code header for HTTP::

        {
         "error": "Unauthorized",
         "data": "Client's credentials are not valid."
         "callback_id": "e67dec5e-1863-11e7-93ae-92361f002671"
        }


    """
    status_code = 403
    message = "Client has no sufficient privileges for this operation."


class PyokoObjectNotFound(PyokoDataAPIError):
    """
    Unauthorized. If client's credential is not valid. The following
    message is sent accompanied by 401 status code header for HTTP::

        {
         "error": "Unauthorized",
         "data": "Client's credentials are not valid."
         "callback_id": "e67dec5e-1863-11e7-93ae-92361f002671"
        }


    """
    status_code = 404
    message = "Object does not exist."


class PyokoDeletedObjectReturned(PyokoDataAPIError):
    """
    Unauthorized. If client's credential is not valid. The following
    message is sent accompanied by 401 status code header for HTTP::

        {
         "error": "Unauthorized",
         "data": "Client's credentials are not valid."
         "callback_id": "e67dec5e-1863-11e7-93ae-92361f002671"
        }


    """
    status_code = 404
    message = "Requested object is marked as deleted."


class PyokoBadRequest(PyokoDataAPIError):
    """
    Unauthorized. If client's credential is not valid. The following
    message is sent accompanied by 401 status code header for HTTP::

        {
         "error": "Unauthorized",
         "data": "Client's credentials are not valid."
         "callback_id": "e67dec5e-1863-11e7-93ae-92361f002671"
        }


    """
    status_code = 400
    message = "Bad request. Request message is malformed. " \
              "Check your model name, fields and query criteria"


class PyokoServerError(PyokoDataAPIError):
    """
    Unauthorized. If client's credential is not valid. The following
    message is sent accompanied by 401 status code header for HTTP::

        {
         "error": "Unauthorized",
         "data": "Client's credentials are not valid."
         "callback_id": "e67dec5e-1863-11e7-93ae-92361f002671"
        }


    """
    status_code = 500
    message = "Server error. Please try again later."


class PyokoDataAPI(object):
    """
    PyokoDataAPI object stands for mediating Pyoko ORM and
    Oauth capabilities to provide a simple and secure data
    access API which can be run as a standalone service.
    
    The recieved message from http or an amqp queue is first
    checked against authentication and authorization rules. 
        
    """

    def __init__(self, message):
        self.auth_message = message.get('auth', None)
        self.model, self.query, self.fields = self.check_message(message)

    def check_auth_message(self):
        """
        Checks auth message. It must not be empty. Auth message 
        must have ``client_screet`` and ``auth_token``.

        Returns:
            bool: True for success or raise related exception.

        """
        if not self.auth_message:
            raise PyokoUnauthorized(message_detail="Please check your auth credentials.")

        client_screet = self.auth_message.get('client_screet', None)
        auth_token = self.auth_message.get('auth_token', None)

        if not all([client_screet, auth_token]):
            raise PyokoUnauthorized(
                message_detail="Please check your auth credentials. "
                               "`client_screet` or `auth_token` is empty")

        return True

    @staticmethod
    def check_message(message):
        """
        Args:
            message (dict): query message
    
        Returns:
            object (QuerySet): pyoko queryset object
        """

        model_name = message.get('model', None)

        if not model_name:
            raise PyokoBadRequest(message_detail="Model name must not be None.")

        try:
            model = model_registry.get_model(model_name)
        except KeyError:
            raise PyokoBadRequest(message_detail="No model found with name {}.".format(model_name))

        fields = message.get('fields', None)

        if fields:
            f = ""
            try:
                for f in fields:
                    model.get_field(f)
            except KeyError:
                raise PyokoBadRequest(message_detail="No field exists with name {}".format(f))

        q = message.get('q', None)

        if not isinstance(q, list) or q:
            raise PyokoBadRequest(message_detail="Please check query string. "
                                                 "It must be a list and can not be empty")

        for qs in q:
            for f in qs.keys():
                ff = f.split('__')
                if len(ff) > 2 or ff[1] not in query_operators:
                    raise PyokoBadRequest(
                        message_detail="Please check query string. "
                                       "Valid operators are {}".format(query_operators))
                try:
                    model.get_field(ff[0])
                except KeyError:
                    raise PyokoBadRequest(
                        message_detail="Please check query string. "
                                       "No field exists with name {}.".format(ff[0]))

        return model, q, fields

    def create_queryset_object(self):
        """
        
        Returns:
    
        """
        qs = None
        q = self.query
        fields = self.fields

        if len(q) == 1:
            qs = self.model.objects.filter(**q)

        if len(q) > 1:
            or_q = {}
            for i in q:
                or_q.update(i)
            qs = self.model.objects.or_filter(**or_q)

        return qs.values(fields) if fields else qs
