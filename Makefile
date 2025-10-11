.PHONY: up down pipeline fmt lint test-quick test-scenarios

up:
	docker compose up -d
	echo "Dashboard → http://localhost:8501"
	echo "NATS → nats://localhost:4222"

down:
	docker compose down -v

pipeline:
	./venv/bin/python -m src.ingest.nats_consumer

fmt:
	./venv/bin/black src || true

lint:
	ruff check src || true

test-quick:
	./venv/bin/python tests/quick_test.py

test-scenarios:
	./venv/bin/python tests/data_publisher.py
