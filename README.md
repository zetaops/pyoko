# README #

Riak Tests 

### Riak Tests repo. Temporary, so nothing fancy here.  ###

Please go
https://youtu.be/ale4K0xsG_E?t=282



## Developer Notes / Possible Gotchas ##

* DO NOT USE PBC in development, it doesn't give proper error messages.

* Since bucket.multiget() works in parallel, it seems it doesn't works reliably. 
    While I haven't extensively tested it yet, I came across some inconsistent results which disappeared after I fallback to get() method.

* Riak's  official Python client depends on existence of **"_yz_rk"** key for distinguishing between old and new search API. 
If we left it out from results, then it assumes the old API and looks for non existent 'id' key, then raises a key error.
To prevent this, we are force inserting it with *field()* calls.

