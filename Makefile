.PHONY: up down collector pipeline fmt lint test-quick test-scenarios

up:
	docker compose up -d
	echo "Dashboard → http://localhost:8501"
	echo "NATS → nats://localhost:4222"

down:
	docker compose down -v

collector:
	go run ./cmd/collector

pipeline:
	./venv/bin/python -m python.ingest.nats_consumer

fmt:
	gofmt -w .
	./venv/bin/black python || true

lint:
	golangci-lint run || true
	ruff check python || true

test-quick:
	./venv/bin/python tests/quick_test.py

test-scenarios:
	./venv/bin/python tests/data_publisher.py
