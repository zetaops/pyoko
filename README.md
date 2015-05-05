# PYOKO #


##Pyoko is a Django-esque lightweight ORM for Riak/Solr (aka Yokozuna)  ##

### Features ###

* Class based data models (schemas).
* Pythonic APIs for Solr's extensive query features.
* Query chaining and caching.
* Use the Solr as DB for indexed data and hit the Riak only when needed.  


#### Developer Notes / Possible Gotchas ####

* DO NOT USE PBC in development, it doesn't give proper error messages.

* Since bucket.multiget() works in parallel, it seems it doesn't works reliably. 
    While I haven't extensively tested it yet, I came across some inconsistent results which disappeared after I fallback to get() method.

* Riak's  official Python client (2.1) depends on existence of **"_yz_rk"** key for distinguishing between old and new search API. 
If we left it out from results, then it assumes the old API and looks for non existent 'id' key, then raises a key error.
To prevent this, we are force inserting it with *field()* calls.

