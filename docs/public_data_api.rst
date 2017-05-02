~~~~~~~~~~~~~~
Pyoko Data API
~~~~~~~~~~~~~~

**Version 0.1**

`Pyoko Data API` is REST and AMQP data access API built on `Pyoko ORM` queryset specifications and Tornado webserver with `oauth`.

It listens on two endpoint, one is a tcp port for http and second is an AMQP queue which is bound to an exchange which gets messages from clients.

===============
DATA ACCESS API
===============

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

Logical Operators
^^^^^^^^^^^^^^^^^
- and
- or

Special Fields
^^^^^^^^^^^^^^
The fields listed below are automatically created with pyoko model definition and all response have these ones by default:

- `timestamp` keeps creation of record
- `updated_at` keeps last update of record
- `deleted` keeps if the record was deleted or not

Query Definitions
^^^^^^^^^^^^^^^^^
- It is defined inside `q` key as a list::

    "q":[filtering criteria here.. ]

- A key value json object means `eq`::

    "q":[ {"name": "Ali"} ] # name is Ali

- A key value json object with one of the `comparison operators` documented above corresponds its lexical or abbreviation meaning::

    "q":[ {"name__in": ["Ali", "Ayse"]} ] # name is one of the following, "Ali" or "Ayse"
    "q":[ {"name__startswith": "A"} ] # name starts with "A"

- Multiple key value json object means that all of pairs is conjoined with "AND"::

    "q":[ {"name": "Ali", "age__gte":24]} ] # name is "Ali" and age is greater than or equal 24.

- Multiple objects means that all objects which are conjoined with "AND" in itsef, are conjoined with "OR"::

    "q":[
          {"name": "Ali"]},
          {"age__lte": 24,]},
        ] # Matches persons whose name is "Ali" OR persons whose age is lower than 24.


=====================
GET / FILTER / SEARCH
=====================
Pyoko provides

GET
^^^

Request:
""""""""
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
"""""""""
A successful get produce response below::

    {
     "data": {"name": "Ali", "is_active": true},
     "callback_id": "e67dec5e-1863-11e7-93ae-92361f002671"
    }

It contains only `data` and request's `callback_id`. And 200 status code is sent for HTTP. `data` has only one object.

FILTER
^^^^^^

Request:
""""""""
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
"""""""""
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


SEARCH
^^^^^^


Errors
^^^^^^
- Unauthorized. If client's credential is not valid. The following message is sent accompanied by 401 status code for HTTP::

    {
     "data": "Unauthorized",
     "callback_id": "e67dec5e-1863-11e7-93ae-92361f002671"
    }

- Forbidden. If client has no sufficient privileges. The following message is sent accompanied by 403 status code for HTTP::

    {
     "data": "Forbidden",
     "callback_id": "e67dec5e-1863-11e7-93ae-92361f002671"
    }

- Not Found. If the object does not exist. The following message is sent accompanied by 404 status code for HTTP::

    {
     "data": "ObjectNotFound",
     "callback_id": "e67dec5e-1863-11e7-93ae-92361f002671"
    }

- Deleted Object Returned. If the object is marked as deleted. The following message is sent accompanied by 404 status code for HTTP::

    {
     "data": "DeletedObjectReturned",
     "callback_id": "e67dec5e-1863-11e7-93ae-92361f002671"
    }

- Bad Request. If request message is malformed or user tries to get a non-existent field or query parameters is not correct. The following message is sent accompanied by 400 status code for HTTP::

    {
     "data": "BadRequest",
     "callback_id": "e67dec5e-1863-11e7-93ae-92361f002671"
    }

- Server Error. If server encounters an error except mentioned above. The following message is sent accompanied by 500 status code for HTTP::

    {
     "data": "ServerError",
     "callback_id": "e67dec5e-1863-11e7-93ae-92361f002671"
    }

License
^^^^^^^

Pyoko is licensed under the `GPL v3.0`_

.. _GPL v3.0: http://www.gnu.org/licenses/gpl-3.0.html
