# README #

Riak Tests 

### Riak Tests repo. Temporary, so nothing fancy here.  ###

Please go
https://youtu.be/ale4K0xsG_E?t=282



## Developer Notes / Possible Gotchas ##

* DO NOT USE PBC in development, it doesn't give proper error messages.

* Since bucket.multiget() works in parallel, it seems it doesn't works reliably. 
    While I haven't extensively tested it yet, I came across some inconsistent results which disappeared after I fallback to get() method.


 

