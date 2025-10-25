.PHONY: up down ps logs

up:
	docker-compose up -d
	@echo "✅ Services started"

down:
	docker-compose down
	@echo "✅ Services stopped"

ps:
	docker-compose ps

logs:
	docker-compose logs -f
