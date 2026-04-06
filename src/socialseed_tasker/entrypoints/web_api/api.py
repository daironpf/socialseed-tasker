"""Ready-to-use FastAPI application for uvicorn.

This module provides a pre-configured FastAPI app with Neo4j repository
that can be run directly with uvicorn:

    uvicorn socialseed_tasker.entrypoints.web_api.api:app --host 0.0.0.0 --port 8000

Or from Python:

    from socialseed_tasker.entrypoints.web_api.api import app
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

from socialseed_tasker.bootstrap.container import Container
from socialseed_tasker.entrypoints.web_api.app import create_app

container = Container.from_env()
repository = container.get_repository()

app = create_app(repository)
