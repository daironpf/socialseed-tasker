# Tasker API — Docker image
# Installs from a pre-built wheel placed at dist/ by tasker init.
# This ensures the container runs the same version as the host.

FROM python:3.12-slim

WORKDIR /app

COPY dist/ ./dist/

RUN pip install --no-cache-dir dist/*.whl && rm -rf dist/

ENV TASKER_NEO4J_URI=bolt://tasker-db:7687
ENV TASKER_NEO4J_USERNAME=neo4j
ENV TASKER_NEO4J_PASSWORD=neoSocial
ENV TASKER_API_HOST=0.0.0.0
ENV TASKER_API_PORT=8000

EXPOSE 8000

CMD ["python", "-m", "socialseed_tasker.infrastructure.web_api.__main__"]
