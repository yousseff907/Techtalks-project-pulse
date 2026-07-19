#Project-Pulse

up:
	docker compose up

up-build:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

restart:
	docker compose down
	docker compose up

clean:
	docker compose down -v

backend-shell:
	docker compose exec backend bash

db-shell:
	docker compose exec postgres psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}

.PHONY: up up-build down logs ps restart clean backend-shell db-shell