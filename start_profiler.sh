poetry export --without-hashes -o requirements.txt

docker volume create profiler_volume

docker build -f dockerfile_profiler -t metalookup_profiler:latest .

docker-compose -f docker-compose-profiler.yml up
