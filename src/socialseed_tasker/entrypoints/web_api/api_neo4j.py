"""Ready-to-use FastAPI application with Neo4j backend for uvicorn.

This module provides a pre-configured FastAPI app with Neo4j-based
repository that can be run directly with uvicorn:

    uvicorn socialseed_tasker.entrypoints.web_api.api_neo4j:app --host 0.0.0.0 --port 8000

Environment variables:
    NEO4J_URI: Bolt connection URI (default: bolt://localhost:7689)
    NEO4J_USER: Database user (default: neo4j)
    NEO4J_PASSWORD: Database password (default: tasker_password)
    NEO4J_DATABASE: Database name (default: neo4j)
"""

import os

from socialseed_tasker.entrypoints.web_api.app import create_app
from socialseed_tasker.storage.graph_database.driver import Neo4jDriver
from socialseed_tasker.storage.graph_database.repositories import Neo4jTaskRepository

uri = os.getenv("NEO4J_URI", "bolt://localhost:7689")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "tasker_password")
database = os.getenv("NEO4J_DATABASE", "neo4j")

driver = Neo4jDriver(uri=uri, user=user, password=password, database=database)
driver.connect()
repository = Neo4jTaskRepository(driver)

app = create_app(repository)
