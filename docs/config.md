# Configuration

## Settings

Some general settings.

File:

`src/lib/settings.py`


## Top level demain defaults

File:

`src/config/config.json`

This file holds standard metadata settings for top level domains.
Currently, it must be manually deployed.

Structure:

```
{
    TOP_LEVEL_DOMAIN_NAME: {
        METADATA_NAME: {
            VALUES: VALUE_TO_BE_PLACED_IN,
            PROBABILITY: PROBABILITY_TO_BE_USED,
            DECISION: DECISION_TO_BE_USED,
        }
    },
    OTHER_TOP_LEVEL_DOMAIN_NAME: ...
}
```