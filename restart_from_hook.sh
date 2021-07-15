#!/bin/bash
echo "Restarting from hook"
cd /code || exit 1
docker-compose down && docker-compose pull && docker-compose -p metadata-picker up -d
