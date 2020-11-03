docker cp oeh-search-meta_extractor_1:/home/extractor/logs/manager.log ./src/logs/manager.log
docker cp oeh-search-meta_extractor_1:/home/extractor/logs/manager_error.log ./src/logs/manager_error.log

docker stop oeh-search-meta_extractor_1