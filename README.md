# PYOKO #


### A Django-esque ORM for Riak KV  ###

#### Supported Features ####
- Nested class based data models (schemas).
- One-To-One, ManyToMany and ManyToOne relations.
- AND queries by using filter() and exclude() methods.
- Or, in, greater than, lower than queries.
- Query chaining and caching.
- Automatic Solr schema creation / update (one way migration).
- Row level access control, permission based cell filtering.
- Self referencing model relations.
- Works with latest Riak (2.1.2)

#### Work in progress ####
- Clenup of invalid/removed relations.

#### Planned ####
- Automatic versioning on write-once buckets.
- Configurable auto-denormalization (aka reactive joins / write-time joins) for relations.
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

    from pyoko import Model, Node, ListNode, field
    
    
    class Permission(Model):
        name = field.String("Name", index=True)
        code = field.String("Code Name", index=True)
    
        class Meta:
            verbose_name = "Permission"
            verbose_name_plural = "Permissions"
    
        def __unicode__(self):
            return "%s %s" % (self.name, self.code)
    
    
    
    
    class Unit(Model):
        name = field.String("Name", index=True)
        address = field.String("Address", index=True, null=True, blank=True)
    
        class Meta:
            verbose_name = "Unit"
            verbose_name_plural = "Units"
    
        def __unicode__(self):
            return self.name
    
    
    class Person(Model):
        first_name = field.String("Name", index=True)
        last_name = field.String("Surname", index=True)
        work = Unit(verbose_name="Work", reverse_name="workers")
        home = Unit(verbose_name="Home", reverse_name="residents")
    
    
        class ContactInfo(Node):
            address = field.String("Address", index=True, null=True, blank=True)
            city = field.String("City", index=True)
            phone = field.String("Phone", index=True)
            email = field.String("Email", index=True)
    
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


```

#### Usage ####

See tests for more usage examples.

```python

    from .models import Person, Unit
    
    user = Person(first_name='Bugs')
    user.last_name = 'Bunny'
    contact_info = user.ContactInfo(email="foo@foo.com", city="Izmir")
    contact_info.phone = "902327055555"
    user.work = Unit(name="Acme").save()
    user.home = Unit(name="Emac").save()
    user.save()

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
