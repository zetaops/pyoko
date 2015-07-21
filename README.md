# PYOKO #


### Pyoko is a Django-esque ORM for Riak  ###

#### Supported Features ####
- Supports Riak 2.1.1
- Nested class based models (schemas).
- AND queries by using filter() and exclude() methods.
- Query chaining and caching.
- Solr schema creation / update (one way migration).
- One-To-One relations with auto denormalization.
- A basic form manager with generic serialization / deserialization. 

#### Work in progress ####
- ManyToMany and ManyToOne relations with auto denormalization
- Row level access control, permission based cell filtering.
- FormSet support for form manager.

#### Planned ####
- Automatic / transparent versioning to write-once buckets.
- More python APIs for Solr queries. 
- Custom migrations with migration history.
- Auto retry of failed writes (on strongly consistent buckets).  
- Picklable models.
- CRDT based models.

---

#### Setup / Configuration ####

Your project should within Python path, so you should be able to import it.

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


- models.py (or models module)

```python

    from pyoko import Model, Node, ListNode, field

    class User(Model):
        name = field.String(index=True)

        
        class AuthInfo(Node):
            username = field.String(index=True)
            email = field.String(index=True)
            password = field.String()

    class Employee(Model):
        usr = User()
        role = field.String(index=True)

```

#### Usage ####

See tests for more usage examples.

```python

        from my_project.models import User, Employee
        
        user = User(name='John').save()
        employee = Employee(role='Coder', usr=user).save()
        emp_from_db = Employee.objects.get(employee.key)
        for emp in Employee.objects.filter(role='Coder'):
            print(emp.usr.name)

```

#### Developer Notes ####

\- Do not use Protocol Buffers in development, it doesn't give proper descriptions for server side errors.


#### Tests ####

Create a bucket type named "pyoko_models" and activate it with following commands:

```bash

#!/bin/sh

# 1 node development:
./bin/riak-admin bucket-type create pyoko_models '{"props":{"last_write_wins":true, "allow_mult":false}}'

# >= 3 node production:
#./bin/riak-admin bucket-type create pyoko_models '{"props":{"consistent":true}}'

./bin/riak-admin bucket-type activate pyoko_models

```
You need to define the following environmental variable to run tests. 

`PYOKO_SETTINGS='tests.settings'`

to create or update schemas run the following command:

` python manage.py update_schema --bucket \<model_name\>,\<model_name\> `

or
 
` python manage.py update_schema --bucket all `

**py.test** command runs all the tests from tests directory.

#### License ####

GPL v3.0
