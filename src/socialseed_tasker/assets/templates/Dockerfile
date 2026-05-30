FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /install /usr/local

COPY src/ ./src/

ENV TASKER_NEO4J_URI=bolt://tasker-db:7687
ENV TASKER_NEO4J_USERNAME=neo4j
ENV TASKER_NEO4J_PASSWORD=neoSocial
ENV TASKER_API_HOST=0.0.0.0
ENV TASKER_API_PORT=8000

EXPOSE 8000

CMD ["python", "-m", "socialseed_tasker.infrastructure.web_api.__main__"]
