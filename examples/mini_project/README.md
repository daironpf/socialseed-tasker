Mini project example

Purpose:
- Demonstrate a minimal end-to-end flow: create issues, attach files, add dependency, generate agent context.

Prerequisites:
- Docker and docker compose installed.
- Run `make dev-up` from repository root to start Neo4j and tasker-dev container.

Run example:
1. Start services:
   make dev-up
2. Run the example:
   make example-run
3. Inspect output:
   cat examples/output.json

Notes:
- The bootstrap script uses the repository's Neo4j adapter and CLI to populate data.
- If the CLI or adapters are not installed in the container, ensure `pip install -e /workspace` is run inside the `tasker-dev` container (Makefile does this).
