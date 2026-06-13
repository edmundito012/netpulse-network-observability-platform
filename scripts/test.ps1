docker compose exec postgres psql -U admin -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'netpulse_test';"

docker compose exec postgres psql -U admin -d postgres -c "DROP DATABASE IF EXISTS netpulse_test;"

docker compose exec postgres psql -U admin -d postgres -c "CREATE DATABASE netpulse_test;"

docker compose exec -e DATABASE_URL="postgresql+psycopg2://admin:admin@postgres:5432/netpulse_test" backend alembic upgrade head

docker compose exec -e DATABASE_URL="postgresql+psycopg2://admin:admin@postgres:5432/netpulse_test" backend pytest