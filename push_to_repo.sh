sh ./build.sh

docker login community.docker.edu-sharing.com

docker tag oeh-search-meta:latest community.docker.edu-sharing.com/oeh-search-meta:latest
docker tag oeh-search-meta_lighthouse:latest community.docker.edu-sharing.com/oeh-search-meta_lighthouse:latest

docker push community.docker.edu-sharing.com/oeh-search-meta:latest
docker push community.docker.edu-sharing.com/oeh-search-meta_lighthouse:latest