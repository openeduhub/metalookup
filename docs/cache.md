# Server internal Caching
To analyze and extract meta information, at first a request to Splash is issued which takes at least 10 seconds,
after that, the lighthouse assessment and the various other extractors usually take another couple of seconds to
complete. Adding up, the total response time is typically at around 20-40 seconds.

To at least mitigate those long response times for URLs that have been analyzed previously, the _MetaLookup_ service
tries to cache results.

## Cache-Control Headers
Caching behaviour of the service can be controlled via the
[`Cache-Control`](https://developer.mozilla.org/de/docs/Web/HTTP/Headers/Cache-Control) headers of incoming requests.
Particularly, the following rules apply:
 - If `Cache-Control` is set to `no-cache` or `no-store`, then the server will not add the current evaluation to its
   cache.
 - If the evaluation is not successful (e.g. because one of the extractors failed), then the incomplete result will
   not be cached.
 - If the `Cache-Control` header is set to `only-if-cached`, then the service will respond with a 400 if the request
   cannot be served from cache.
 - Currently, there is no mechanism to force a cache refresh or expiration via the `Cache-Control` headers. However, the
   response headers should include an `Age` header when cached data is returned.
