# Cache

## Rational

Evaluation is currently slow, requiring more than 10s per URL.
Since crawlers and human users use the service, a speed-up is required.

For some metadata, results in the domain are probably (!) comparable and could be reused. One example is GDPR.

## Solution

Caching data from former evaluations and reusing them in current evaluations if:
- the metadata is whitelisted for caching
- the evaluation is not older than four weeks from now
- at least five data sets have been cached in the past

The cached data is loaded, whenever a metadata is started for evaluation. If there is cached data, that data is loaded
and `cached` is added to `explanation`. Apart from that, nothing changes to the outside world.
Evaluation is then skipped.

`values` are not cached, only `isHappyCase`, `probability` and `explanation`.

## Obstacles

The cache may become corrupt, e.g-, due to repeated evaluation of the same website or database issues

Websites may change faster than on a four-week cycle. Thus, a cache reset is needed. This is possible through the
API endpoint `/cache/reset` which is disabled in production environments.
