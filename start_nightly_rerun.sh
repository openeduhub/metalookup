poetry export --without-hashes -o requirements.txt

docker build -f dockerfile_nightly_rerun -t metalookup_nightly_rerun:latest .

docker-compose -f docker-compose-nightly_rerun.yml up
