poetry build

docker volume create db_volume

docker build -t docker.edu-sharing.com/projects/oeh-redaktion/edusharing-projects-oeh-redaktion-metalookup-api:latest .

docker build -f dockerfile_lighthouse -t docker.edu-sharing.com/projects/oeh-redaktion/edusharing-projects-oeh-redaktion-metalookup-lighthouse:latest .
