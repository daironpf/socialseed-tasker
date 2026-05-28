FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir socialseed-tasker

ENV TASKER_NEO4J_URI=bolt://tasker-db:7687
ENV TASKER_NEO4J_USERNAME=neo4j
ENV TASKER_NEO4J_PASSWORD=neoSocial
ENV TASKER_API_HOST=0.0.0.0
ENV TASKER_API_PORT=8000

EXPOSE 8000

CMD ["tasker", "serve", "--host", "0.0.0.0", "--port", "8000"]
