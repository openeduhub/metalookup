poetry build

docker volume create db_volume

docker build -t community.docker.edu-sharing.com/oeh-search-meta:latest .

docker build -f dockerfile_lighthouse -t community.docker.edu-sharing.com/oeh-search-meta_lighthouse:latest .
