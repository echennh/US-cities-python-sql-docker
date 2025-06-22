#!/usr/bin/env bash
# this script is a little stop light to make sure the mysql db is up and running before letting the python scripts run against it
set -euo pipefail

host="${DB_HOST:-db}"
port="${DB_PORT:-3306}"

echo "⌛ Waiting for MySQL at ${host}:${port} …"
until mysqladmin ping -h"${host}" -P"${port}" --silent; do
  sleep 1
done
echo "✅ MySQL is up – starting application"

exec "$@"
