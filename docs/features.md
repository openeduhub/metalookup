# Features

A feature is a kind of metadata extracted from the desired url.
This can be header information regarding security, whether the url contains advertisement,
PG18 content or complies to GDPR.
Many features are opinionated and require feedback from production for hardening.
Some features "react" hysterically, e.g., flag the website as insecure because one cookie has `secure=False`.
Other features are insensitive to certain cases, e.g., whether a website confirms to GDPR is difficult to decide.

Thus, please take all output with a grain of salt.

## Understanding decision and probability

The service returns the values

- `isHappyCase`
- `probability`

for each evaluated feature.

`isHappyCase` is either:

- `True`:
  Knockout for this metadata is true.:
    - advertisement: if true, ads have been found
    - GDPR: if true, the website is confirming to GDPR
- `False`:
    - either the metadata has not been found in the website (e.g., ads)
      or the website is not conforming to the requirements (e.g., is not iframe embeddable)
- `Unknown`:
  - it is unclear, whether this metadata leads to knock-out or not.
  - A human should double check this metadata prior to final decision

The `probability` scales from `0` to `1`.

- `0` indicates that nothing is certain, i.e., whether `isHappyCase` is True or False is irrelevant.
  - generally, `isHappyCase` will be `Unknown` in this case
- `1` indicates certainty, i.e., either False or True are certain.

Both `isHappyCase` and `probability` are determined specifically for each feature based on developer-chosen thresholds
and methods.
Therefore, all results are opinionated and heavily biased.
With more production data, these features may be improved.

`True` and `False` are not strict opposites, i.e., just because something is false does not mean it is not true.
E.g., it may indicate that the algorithm does not find suitable results or only partial agreement is found
(as in the case of GDPR).
In line with that, a 30% probability of True does not mean it is 70% False.

## Adding new features for detection

To add a new feature, it must inherit from MetadataBase.

The class must be included in

1. `src/features/metadata_manager.py:__setup_extractors`
2. `app.models.ExtractorTags`
3. `app.models.ListTags`

Furthermore, the cache must be extended, update
- `db.models.CacheEntry`
- `app.schemas.CacheSchema`

Potentially, the cache must be reset through the respective API endpoint.

### Example

A good example to see minimum requirements for a feature can be found in `src/features/javascript.py`.
