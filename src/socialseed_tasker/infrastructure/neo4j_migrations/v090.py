"""Migration for SocialSeed Tasker v0.9.0.

Adds vector indexes for RAG, constraints for Code-as-Graph,
and indexes for Reasoning logs.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from neo4j.exceptions import Neo4jError

if TYPE_CHECKING:
    from socialseed_tasker.infrastructure.neo4j_driver import Neo4jDriver

logger = logging.getLogger(__name__)

MIGRATION_QUERIES = [
    # 1. Vector Indexes (RAG)
    "CREATE VECTOR INDEX issue_embeddings IF NOT EXISTS FOR (i:Issue) ON (i.embedding) OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}",
    
    # 2. Code-as-Graph Constraints
    "CREATE CONSTRAINT code_file_id IF NOT EXISTS FOR (f:CodeFile) REQUIRE f.id IS UNIQUE",
    "CREATE CONSTRAINT code_symbol_id IF NOT EXISTS FOR (s:CodeSymbol) REQUIRE s.id IS UNIQUE",
    "CREATE CONSTRAINT code_import_id IF NOT EXISTS FOR (i:CodeImport) REQUIRE i.id IS UNIQUE",
    
    # 3. Reasoning Nodes Constraints & Indexes
    "CREATE CONSTRAINT reasoning_node_id IF NOT EXISTS FOR (r:ReasoningNode) REQUIRE r.id IS UNIQUE",
    "CREATE INDEX reasoning_timestamp IF NOT EXISTS FOR (r:ReasoningNode) ON (r.timestamp)",
    "CREATE INDEX reasoning_issue_id IF NOT EXISTS FOR (r:ReasoningNode) ON (r.issue_id)",
    
    # 4. Agent Constraints
    "CREATE CONSTRAINT agent_id IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE",
    
    # 5. Relationship Indexes
    "CREATE INDEX code_calls IF NOT EXISTS FOR ()-[r:CALLS]->() ON (r.timestamp)",
    "CREATE INDEX code_depends IF NOT EXISTS FOR ()-[r:DEPENDS_ON]->() ON (r.timestamp)",
    "CREATE INDEX agent_thought IF NOT EXISTS FOR ()-[r:THOUGHT]->() ON (r.timestamp)",
]

ROLLBACK_QUERIES = [
    "DROP INDEX issue_embeddings IF EXISTS",
    "DROP CONSTRAINT code_file_id IF EXISTS",
    "DROP CONSTRAINT code_symbol_id IF EXISTS",
    "DROP CONSTRAINT code_import_id IF EXISTS",
    "DROP CONSTRAINT reasoning_node_id IF EXISTS",
    "DROP INDEX reasoning_timestamp IF EXISTS",
    "DROP INDEX reasoning_issue_id IF EXISTS",
    "DROP CONSTRAINT agent_id IF EXISTS",
    "DROP INDEX code_calls IF EXISTS",
    "DROP INDEX code_depends IF EXISTS",
    "DROP INDEX agent_thought IF EXISTS",
]

def run_migration(driver: Neo4jDriver) -> bool:
    """Run the v0.9.0 migration queries."""
    logger.info("Starting Neo4j v0.9.0 migration...")
    success = True
    
    with driver.driver.session(database=driver.database) as session:
        for query in MIGRATION_QUERIES:
            try:
                session.run(query)
                logger.info("Successfully executed: %s", query[:50] + "...")
            except Neo4jError as exc:
                logger.error("Failed to execute query: %s\nError: %s", query, exc)
                success = False
                break
                
    if success:
        logger.info("Neo4j v0.9.0 migration completed successfully.")
    else:
        logger.error("Neo4j v0.9.0 migration failed.")
        
    return success

def rollback_migration(driver: Neo4jDriver) -> bool:
    """Roll back the v0.9.0 migration queries."""
    logger.info("Rolling back Neo4j v0.9.0 migration...")
    success = True
    
    with driver.driver.session(database=driver.database) as session:
        for query in ROLLBACK_QUERIES:
            try:
                session.run(query)
                logger.info("Successfully executed rollback: %s", query[:50] + "...")
            except Neo4jError as exc:
                logger.error("Failed to execute rollback query: %s\nError: %s", query, exc)
                success = False
                
    return success
