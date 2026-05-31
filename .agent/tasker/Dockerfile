# Tasker API — Docker image
# Builds from local source. Requires pyproject.toml and src/ at build context.
# To use a pre-built image from a registry, replace the build block in
# docker-compose.yml with `image: your-registry/tasker-api:tag`.

FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir -e .

ENV TASKER_NEO4J_URI=bolt://tasker-db:7687
ENV TASKER_NEO4J_USERNAME=neo4j
ENV TASKER_NEO4J_PASSWORD=neoSocial
ENV TASKER_API_HOST=0.0.0.0
ENV TASKER_API_PORT=8000

EXPOSE 8000

CMD ["python", "-m", "socialseed_tasker.infrastructure.web_api.__main__"]