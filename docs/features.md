# Features
A feature is a kind of metadata extracted from the desired url with a dedicated `Extractor` class.
This can be header information regarding security, whether the url contains advertisement,
PG18 content or complies to GDPR.
Many extractors are opinionated and require feedback from production for hardening.
Some extractors "react" hysterically, e.g., flag the website as insecure because one cookie has `secure=False`.
Other extractors are insensitive to certain cases, e.g., whether a website confirms to GDPR is difficult to decide.

Thus, please take all output with a grain of salt, all results are opinionated and heavily biased, with more production
data, these features may be improved!

## Understanding the extractors decision
Every extractor results in exactly one extracted feature in the response. This extractor specific response part looks
as follows:

```json
{
  "stars": 3,
  "explanation": "Some human readable message",
  "extra": {
    "foo1": "A structure that depends on the implementation of the extractor.",
    "foo2": "It contains additional information about how the extractor came to it's star rating and explanation."
  }
}
```

For example, the structure for the `Licence` extractor could look as follows:

```json
{
  "stars": 5,
  "explanation": "Content appears to be licenced with CC0.",
  "extra": {
    "guess": "CC0",
    "total": 5,
    "counts": {"CC_BY": 1, "CC0": 4}
  }
}
```

In case an extractor is not able to complete (due to internal errors), then the respective extractor will report this
error in the following form:

```json
{
  "error": "What went wrong, eventually including a stack trace where the error originated."
}
```

## Adding new features for detection
To add a new feature,

 - create a new class that implements the [`Extractor`](../src/metalookup/core/extractor.py) interface in the `features`
   module.
 - Add the new class to the `setup` call of the [`MetaDataManager`](../src/metalookup/core/metadata_manager.py)
 - Add a field that matches your extractors `key` to the [output model](../src/metalookup/app/models.py)

Note, that such a change can be considered a breaking change, as the response model of the API gets modified. Also, it
may make sense to truncate the cache, as otherwise cached results will not include the newly added feature.
