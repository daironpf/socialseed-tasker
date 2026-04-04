"""Ready-to-use FastAPI application for uvicorn.

This module provides a pre-configured FastAPI app with file-based
repository that can be run directly with uvicorn:

    uvicorn socialseed_tasker.entrypoints.web_api.api:app --host 0.0.0.0 --port 8000

Or from Python:

    from socialseed_tasker.entrypoints.web_api.api import app
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

from socialseed_tasker.bootstrap.container import Container
from socialseed_tasker.entrypoints.web_api.app import create_app
from socialseed_tasker.storage.local_files.repositories import FileTaskRepository

container = Container.from_env()
repository = FileTaskRepository(container.config.storage.file_path)

app = create_app(repository)
