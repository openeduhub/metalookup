
# Adding new features for detection

To add a new feature, it must inherit from MetadataBase.

The class must be included in 

1. "src/features/metadata_manager.py:_create_extractors"
2. app.api.ExtractorTags
3. app.api.ListTags
