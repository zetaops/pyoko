# PYOKO #


### A Django-esque ORM for Riak KV  ###

#### Supported Features ####
- Supports latest Riak (2.1.1)
- Nested class based data models (schemas).
- AND queries by using filter() and exclude() methods.
- Query chaining and caching.
- Automatic Solr schema creation / update (one way migration).
- One-To-One, ManyToMany and ManyToOne relations with auto denormalization (aka reactive joins / write-time joins)
- Row level access control, permission based cell filtering.

#### Work in progress ####
- More pythonic APIs for Solr's extensive query features. (OR queries, searching in list of values)
- Self referencing model relations.

#### Planned ####
- Auto retry of failed writes (on strongly consistent buckets).
- Automatic versioning on write-once buckets.
- Custom migrations with migration history.
- CRDT based models.

---

#### Setup / Configuration ####

Your project should within Python path, so you could be able to import it.

Base file structure of a Pyoko based project;

- manage.py:

```python

    from pyoko.manage import *
    environ.setdefault('PYOKO_SETTINGS', '<PYTHON.PATH.TO.PROJECT>.settings')
    ManagementCommands(argv[1:])

```

- settings.py

```python

    RIAK_SERVER = 'localhost'
    RIAK_PROTOCOL = 'http'
    RIAK_PORT = '8098'

    # if not defined, will be searched within same directory as settings.py
    # MODELS_MODULE = '<PYTHON.PATH.OF.MODELS.MODULE>'

```


- models.py (or models package)

```python

    from pyoko import Model, Node, field

    class User(Model):
        first_name = field.String("Name", index=True)
        last_name = field.String("Surname", index=True)


        class ContactInfo(Node):
            address = field.String("Address", index=True, null=True, blank=True)
            city = field.String("City", index=True)
            phone = field.String("Phone", index=True)
            email = field.String("Email", index=True)

    class Employee(Model):
        usr = User()
        role = field.String(index=True)

```

#### Usage ####

See tests for more usage examples.

```python

        from my_project.models import User, Employee

        user = User(name='John')
        user_cont_info = user.ContactInfo(email="foo@foo.com", city="Izmir")
        user_cont_info.phone = "902327055555"
        user.save()
        employee = Employee(role='Coder', usr=user).save()
        emp_from_db = Employee.objects.get(employee.key)
        for emp in Employee.objects.filter(role='Coder'):
            print(emp.usr.name, emp.usr.ContactInfo.email)

```

#### Developer Notes ####

\- Do not use Protocol Buffers in development, it doesn't give proper descriptions for server side errors.


#### Tests ####

Create a bucket type named "pyoko_models" and activate it with following commands:

```bash

#!/bin/sh

# 1 node development:
./bin/riak-admin bucket-type create pyoko_models '{"props":{"last_write_wins":true, "allow_mult":false, "n_val":1}}'

# >= 3 node production:
#./bin/riak-admin bucket-type create pyoko_models '{"props":{"consistent":true}}'

./bin/riak-admin bucket-type activate pyoko_models

```
You need to define the following environmental variable to run tests.

`PYOKO_SETTINGS='tests.settings'`

to create or update schemas run the following command:

` python manage.py migrate --model \<model_name\>,\<model_name\> `

or

` python manage.py migrate --model all `

**py.test** command runs all the tests from tests directory.

#### License ####

GPL v3.0
