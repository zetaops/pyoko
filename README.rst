.. image:: https://readthedocs.org/projects/pyoko/badge/?version=latest
    :target: http://pyoko.readthedocs.org/en/latest/?badge=latest
    :alt: Documentation Status

Pyoko: A Django-esque NoSQL ORM for Riak KV 2.1.4
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Features
^^^^^^^^^

-  Nested class based data models (schemas).
-  One-To-One, ManyToMany and ManyToOne relations.
-  AND queries by using filter() and exclude() methods.
-  Or, in, greater than, lower than queries.
-  Query chaining and caching.
-  Automatic Solr schema creation / update (one way migration).
-  Row level access control, permission based cell filtering.
-  Self referencing model relations.
-  Automatic versioning on write-once buckets.
-  Customizable activity logging to write-once buckets.
-  Works with Riak 2.1 and up.


Planned
^^^^^^^

-  Configurable auto-denormalization (aka reactive joins / write-time
   joins) for relations.
-  Custom migrations with migration history.
-  CRDT based models.


API Documentation
^^^^^^^^^^^^^^^^^^
Read the API documentation at pyoko.readthedocs.org_.

.. _pyoko.readthedocs.org: http://pyoko.readthedocs.org/en/latest/api-documentation.html


Quick Start
^^^^^^^^^^^^^^^^^^^^^

Your project should within Python path, so you could be able to import
it.

Base file structure of a Pyoko based project;

-  manage.py:

.. code:: python

        from pyoko.manage import *
        environ.setdefault('PYOKO_SETTINGS', '``<PYTHON.PATH.TO.PROJECT>``.settings')
        ManagementCommands(argv[1:])

-  settings.py

.. code:: python

        RIAK_SERVER = 'localhost'
        RIAK_PROTOCOL = 'http'
        RIAK_PORT = '8098'

        # if not defined, will be searched within same directory as settings.py
        # MODELS_MODULE = '<PYTHON.PATH.OF.MODELS.MODULE>'

-  models.py (or models package)

.. code:: python

        from pyoko import Model, Node, ListNode, field

        class Permission(Model):
            name = field.String("Name")
            code = field.String("Code Name")

            class Meta:
                verbose_name = "Permission"
                verbose_name_plural = "Permissions"

            def __unicode__(self):
                return "%s %s" % (self.name, self.code)


        class Unit(Model):
            name = field.String("Name")
            address = field.String("Address", null=True, blank=True)

            class Meta:
                verbose_name = "Unit"
                verbose_name_plural = "Units"

            def __unicode__(self):
                return self.name


        class Person(Model):
            first_name = field.String("Name")
            last_name = field.String("Surname")
            work = Unit(verbose_name="Work", reverse_name="workers")
            home = Unit(verbose_name="Home", reverse_name="residents")


            class ContactInfo(Node):
                address = field.String("Address", null=True, blank=True)
                city = field.String("City")
                phone = field.String("Phone")
                email = field.String("Email")

            class Permissions(ListNode):
                perm = Permission()

                def __unicode__(self):
                    return self.perm

            def __unicode__(self):
                return "%s %s" % (self.first_name, self.last_name)

            def get_permission_codes(self):
                return [p.perm.code for p in self.Permissions]

            def add_permission(self, perm):
                self.Permissions(permission=perm)
                self.save()

            def has_permission(self, perm):
                return perm in self.Permissions

            def has_permission_code(self, perm_code):
                perm = Permission.object.get(code=perm_code)
                return self.has_permission(perm)


Creating objects, Making Queries
--------------------------------

.. code:: python

        from .models import Person, Unit, Permission

        user = Person(first_name='Bugs')
        user.last_name = 'Bunny'
        contact_info = user.ContactInfo(email="foo@foo.com", city="Izmir")
        contact_info.phone = "55555555"
        user.work = Unit(name="Acme").save()
        user.home = Unit(name=  "Emac").save()
        user.save()


Notes
------
- Do not use Protocol Buffers in development, it doesn't give proper descriptions for server side errors.

- Use CamelCase for model, node and listnodes

- Use underscored names for fields

- ``_id`` and ``_set`` are reserved suffixes for internal use. Do not suffix your fields with ``_id`` or ``_set``.

- ``deleted`` and ``timestamp`` are implicitly added fields. Do not use these words as field names.

- Set DEBUG to 1 or greater integer to enable query debugging which collects query stats under sys.\_debug\_db\_queries:

.. code:: python

    In [1]: import sys
    In [2]: sys._debug_db_queries
    Out[2]:
    [
     {'BUCKET': 'models_personel',
      'QUERY': '-deleted:True',
      'QUERY_PARAMS': {'rows': 1, 'sort': b'timestamp desc', 'start': 0},
      'TIME': 0.0056,
      'TIMESTAMP': 1452245987.258094},
      {'BUCKET': 'models_personel',
        'KEY': 'Aqq2O50XGqerJsfOPquqDmINbyM',
        'TIME': 0.00229,
        'TIMESTAMP': 1452245980.413088},
      ]

- Set value of DEBUG to 5 or a greater integer to get instant print out of each executed query.

.. code:: python

    In [1]: Personel.objects.filter(ad__startswith='Al')
    Out[1]: QRY => ad:Al* AND -deleted:True
    [<Personel: ali g.>]

Tests
^^^^^

Create a bucket type named "pyoko\_models" and activate it with following commands:

.. code:: bash


    #!/bin/sh

    # 1 node development:
    ./bin/riak-admin bucket-type create pyoko_models '{"props":{"last_write_wins":true, "dvv_enabled":false, "allow_mult":false, "n_val":1}}'

    # >= 3 node production:
    #./bin/riak-admin bucket-type create pyoko_models '{"props":{"consistent":true}}'

    ./bin/riak-admin bucket-type activate pyoko_models

You need to define the following environmental variable to run tests.

``PYOKO_SETTINGS='tests.settings'``

to create or update schemas run the following command:

``python manage.py migrate --model User,Permission``

or

``python manage.py migrate --model all``

**py.test** command runs all the tests from tests directory.


Support
-------

Feel free to fork this and send back Pull Requests for any
defects or features that you want to contribute back.
Opening issues here is also recommended.

If you need to get the attention of the ZetaOps team send an email
to info ~at~ zetaops.io.
Commercial support from ZetaOps_ requires a valid support contract.

.. _ZetaOps: http://zetaops.io

Authors
=======

* Evren Esat Özkan
* Ali Rıza Keleş
* Gökhan Boranalp


License
^^^^^^^

Pyoko is licensed under the `GPL v3.0`_

.. _GPL v3.0: http://www.gnu.org/licenses/gpl-3.0.html
