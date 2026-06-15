SHELL := /bin/bash

.PHONY: dev_infra


infra_postgres:
	docker compose -p example_project -f docker-compose.yml up -d --build postgres
