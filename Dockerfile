FROM python:3.12-slim-bookworm
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 PATH="/usr/lib/jvm/java-17-openjdk-amd64/bin:${PATH}" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jre-headless && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml poetry.lock* ./
RUN pip install --no-cache-dir poetry && poetry config virtualenvs.create false
RUN poetry install --only main --no-root
COPY . .
RUN poetry install --only main
CMD ["python", "-m", "climatewatch.interfaces.cli", "--help"]
