# PYOKO #


##Pyoko is a Django-esque lightweight ORM for Riak/Solr (aka Yokozuna)  ##

### Features ###
*Features which are not yet implemented shown as italic*

* Nested class based data models (schemas).
* Query chaining and caching.
* Pythonic APIs for Solr's extensive query features. *(incomplete)*
* *Abstract base models.*
* *Lazy loaded model data.*
* *Schema migrations, with custom and backwards migration support.* 
* Three data source: Redis > Solr > Riak (configurable)
    * *Redis based caching of GET requests.*
    * *Partially or fully store and get from Solr*
    * Hit the Riak only when needed.


#### Developer Notes / Possible Gotchas ####

* DO NOT USE PBC in development, it doesn't give proper descriptions for server side errors.

* Riak's  official Python client (2.1) depends on existence of **"_yz_rk"** key for distinguishing between old and new search API. 
If we left it out from results, then it assumes the old API and looks for non existent 'id' key, then raises a key error.
To prevent this, we implicitly inserting it with field() calls.

#### Tests ####

Tests needs a locally running Riak instance at port 8098.

**py.test** command runs all the tests from tests directory.
