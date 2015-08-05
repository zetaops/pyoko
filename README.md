# PYOKO #


### A Django-esque ORM for Riak KV  ###

#### Supported Features ####
- Supports Riak 2.1.1
- Nested class based data models (schemas).
- AND queries by using filter() and exclude() methods.
- Query chaining and caching.
- Automatic Solr schema creation / update (one way migration).
- One-To-One, ManyToMany and ManyToOne relations with auto denormalization

#### Work in progress ####
- Row level access control, permission based cell filtering.
- Self referencing model relations.

#### Planned ####
- More pythonic APIs for Solr's extensive query features.
- Custom and backwards migrations.
- Auto retry of failed writes (on strongly consistent buckets).  
- Automatic versioning on write-once buckets.
- Picklable models.
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
