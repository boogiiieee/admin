# publication_admin

## Install

```bash
git clone git@gitlab.com:docets/backend/publication-admin.git
pipx install poetry
poetry install
```

## Development

```bash
# Create .env file
cp example.env .env
# And adjust desired envs

# Run dev server locally...
make run

# ...or using Docker
docker compose up

# Run tests
make test

# Generate HTML coverage report and inspect
make coverage

# Format your code before commit
make format
```

## Migrations

```bash
# Create new migration
alembic revision --autogenerate -m <migration-verbose-name> --rev-id <ID-of-migration>

# Migrate
make migrate
```
