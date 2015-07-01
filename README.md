# PYOKO #


## Pyoko is a Django-esque lightweight ORM for Riak/Solr (aka Yokozuna)  ##

### Features ###

#### Supported ####
- Nested class based data models (schemas).
- Query chaining and caching.
- Automatic Solr schema creation / update (one way migration).
- ManyToMany and ManyToOne relations with auto denormalization

#### Work in progress ####
- Pythonic APIs for Solr's extensive query features. 

#### Planned ####
- Row level access control, permission based cell filtering. 
- Custom and backwards migrations.
- Picklable models

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


```python

        from my_project.models import User, Employee
        
        user = User(name='John').save()
        employee = Employee(role='Coder', usr=user).save()
        emp_from_db = Employee.objects.get(employee.key)
        for emp in Employee.objects.filter(role='Coder'):
            print(emp.usr.name)

```

#### Developer Notes ####

- Do not use Protocol Buffers in development, it doesn't give proper descriptions for server side errors.


#### Tests ####

Tests needs a locally running Riak instance at port 8098.

Create a bucket type named models and activate it with following commands:

./riak-admin bucket-type create models
./riak-admin bucket-type activate models

You need to define the following environmental variable to run tests. 

PYOKO_SETTINGS='tests.settings'

to create schemas run command:

python manage.py update_schema --bucket <model_name>,<model_name>,...

**py.test** command runs all the tests from tests directory.

#### License ####

GPL v3.0
