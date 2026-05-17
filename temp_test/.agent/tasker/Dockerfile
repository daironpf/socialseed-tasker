FROM python:3.10-slim

WORKDIR /app

# Install socialseed-tasker and its dependencies
# In a production scenario, this would pull from PyPI.
# For now, we assume the environment has access or we use the pre-built image.
RUN pip install --no-cache-dir socialseed-tasker httpx

# Environment variables for Neo4j configuration
ENV TASKER_NEO4J_URI=bolt://tasker-db:7687
ENV TASKER_NEO4J_USERNAME=neo4j
ENV TASKER_NEO4J_PASSWORD=neoSocial
ENV TASKER_API_HOST=0.0.0.0
ENV TASKER_API_PORT=8000

# Expose the API port
EXPOSE 8000

# Start the Tasker API server
CMD ["tasker", "serve", "--host", "0.0.0.0", "--port", "8000"]
