up:
	docker compose up --build
down:
	docker compose down
test:
	PYTHONPATH=. pytest backend/tests -q
seed:
	PYTHONPATH=. python scripts/demo.py
reset:
	curl -X POST http://localhost:8000/api/demo/reset
logs:
	docker compose logs -f
