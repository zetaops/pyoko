# PYOKO #


## Pyoko is a Django-esque lightweight ORM for Riak/Solr (aka Yokozuna)  ##

### Features ###

#### Implemented ####
- Nested class based data models (schemas).
- Query chaining and caching.
- Automatic Solr schema creation / update.

#### Work in progress ####
- Pythonic APIs for Solr's extensive query features. 
- Row level access control, permission based cell filtering. 

#### Planned ####
- Advanced ManyToMany and ManyToOne relations with auto denormalization 
- Schema migrations, with custom and backwards migration support.
- Three tiered data storage: Redis > Solr > Riak (configurable)
    - Redis based caching of GET requests.
    - Partially or fully store and get data from Solr
    - Hit the Riak only when needed. (Lazy loaded models)
- Picklable models
---

#### Configuration ####

See Tests section.

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
