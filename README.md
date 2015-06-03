# PYOKO #


##Pyoko is a Django-esque lightweight ORM for Riak/Solr (aka Yokozuna)  ##

### Features ###
*Features which are not yet implemented shown as italic*

* Nested class based data models (schemas).
* Query chaining and caching.
* Pythonic APIs for Solr's extensive query features. *(incomplete)*
* *Abstract base models.*
* *Lazy loaded models.*
* *Many To Many and Many to One relations with auto denormalization* 
* *Schema migrations, with custom and backwards migration support.* 
* Three tiered data storage: Redis > Solr > Riak (configurable)
    * *Redis based caching of GET requests.*
    * *Partially or fully store and get data from Solr*
    * Hit the Riak only when needed.


#### Developer Notes ####

* DO NOT USE PBC in development, it doesn't give proper descriptions for server side errors.



#### Tests ####

Tests needs a locally running Riak instance at port 8098.

**py.test** command runs all the tests from tests directory.
