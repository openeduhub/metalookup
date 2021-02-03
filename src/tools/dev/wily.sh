# cd ../../..
poetry run wily build src
poetry run wily rank --asc -l 4 | grep ".py"

poetry run wily graph src/features/metadata_base.py mi
poetry run wily graph src/features/gdpr.py mi
poetry run wily graph src/features/extract_from_files.py mi
poetry run wily graph src/features/website_manager.py mi