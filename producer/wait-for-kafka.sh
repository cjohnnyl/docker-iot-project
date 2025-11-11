#!/bin/sh
# wait-for-kafka.sh

set -e

host="$1"
shift
cmd="$@"

until python3 -c "from kafka import KafkaAdminClient; KafkaAdminClient(bootstrap_servers='$host', request_timeout_ms=10000).close()" 2>/dev/null; do
  >&2 echo "Kafka is unavailable - sleeping"
  sleep 2
done

>&2 echo "Kafka is up - executing command"
exec $cmd
