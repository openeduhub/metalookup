# Features

## Understanding decision and probability

The service returns the values

- decision
- probability

for each evaluated metadata.

Decision is either:

- True: 
  the metadata is true or present, e.g.:
    - advertisement: if true, ads have been found
    - GDPR: if true, the website is confirming to GDPR
- False:
    - either the metadata has not been found in the website (e.g., ads) 
      or the website is not conforming to the requirements (e.g., is not iframe embeddable)

The probability scales from 0 to 1.
0 indicates that nothing is certain, i.e., whether the decision is True or False is irrelevant.
1 indicates certainty, i.e., either False or True are certain.

Both decision and probability are determined specifically for each metadata based on developer-chosen thresholds and
methods.
Therefore, all results are opinionated and heavily biased.
With more data, these methods should be refactored.

True and False are not strict opposites, i.e., just because something is false does not mean it is not true.
E.g., it may indicate that the algorithm does not find suitable results or only partial agreement is found 
(as in the case of GDPR).
In line with that, a 30% probability of True does not mean it is 70% False.

## Adding new features for detection

To add a new feature, it must inherit from MetadataBase.

The class must be included in 

1. "src/features/metadata_manager.py:_create_extractors"
2. app.api.ExtractorTags
3. app.api.ListTags
