"""Main entry point for running the API directly with python -m."""

import uvicorn

from socialseed_tasker.bootstrap.container import Container
from socialseed_tasker.entrypoints.web_api.app import create_app


def main() -> None:
    """Run the API server."""
    container = Container.from_env()
    repository = container.get_repository()
    app = create_app(repository)

    config = uvicorn.Config(
        app,
        host=container.config.api_host,
        port=container.config.api_port,
        reload=container.config.debug,
        log_level="info" if not container.config.debug else "debug",
    )
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    main()
