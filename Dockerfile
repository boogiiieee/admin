FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends make && apt-get clean

RUN pip install --no-cache-dir poetry==1.7.1
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-root

COPY . ./

EXPOSE 8000

ENTRYPOINT ["poetry", "run"]
CMD ["uvicorn", "publication_admin.main:app", "--host", "0.0.0.0", "--port", "8000"]
