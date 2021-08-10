# cd ../../..
poetry run wily build src
poetry run wily rank --asc -l 4 | grep ".py"

file=src/features/metadata_base.py

poetry run wily graph $file mi
poetry run wily graph $file raw.sloc
poetry run wily graph $file cyclomatic.complexity
