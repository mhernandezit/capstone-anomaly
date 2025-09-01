.PHONY: up down collector pipeline fmt lint

up:
	docker compose up -d
	echo "Dashboard → http://localhost:8501"
	echo "NATS → nats://localhost:4222"

down:
	docker compose down -v

collector:
	go run ./cmd/collector

pipeline:
	python -m python.ingest.nats_consumer

fmt:
	gofmt -w .
	black python || true

lint:
	golangci-lint run || true
	ruff check python || true
