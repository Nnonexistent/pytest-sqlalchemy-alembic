SHELL := /bin/bash
.DEFAULT_GOAL := help


help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

.PHONY: infra_postgres
infra_postgres:  ## Start PostgreSQL container
	@docker compose -p example_project -f docker-compose.yml up -d --build postgres

.PHONY: infra_mariadb
infra_mariadb:  ## Start MariaDB container
	@docker compose -p example_project -f docker-compose.yml up -d --build mariadb

.PHONY: infra_down
infra_down:  ## Stop and remove all containers
	@docker compose -p example_project -f docker-compose.yml down

.PHONY: infra_down_volume_purge
infra_down_volume_purge:  ## Stop and delete all volumes used by the project
	@docker compose -p example_project -f docker-compose.yml down --volumes
