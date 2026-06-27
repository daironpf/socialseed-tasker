"""Schema migration script for v0.9.0.

This script creates vector indexes and additional indexes required for:
- RAG (vector embeddings)
- Code-as-Graph relationships
- Reasoning relationships

Usage:
    python migrate_v090.py [--rollback]
"""

import argparse
import logging
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MIGRATION_QUERIES = [
    ("issue_embeddings", 
     "CREATE VECTOR INDEX issue_embeddings IF NOT EXISTS FOR (i:Issue) ON (i.embedding) OPTIONS {indexConfig: {vector: {dimension: 1536, similarityFunction: 'cosine'}}}"),
    ("code_calls", 
     "CREATE INDEX code_calls IF NOT EXISTS FOR ()-[r:CALLS]->() ON (r.timestamp)"),
    ("code_depends_issue", 
     "CREATE INDEX code_depends_issue IF NOT EXISTS FOR ()-[r:DEPENDS_ON]->() ON (r.timestamp)"),
    ("agent_thought", 
     "CREATE INDEX agent_thought IF NOT EXISTS FOR ()-[r:THOUGHT]->() ON (r.timestamp)"),
]

ROLLBACK_QUERIES = [
    "DROP INDEX issue_embeddings IF EXISTS",
    "DROP INDEX code_calls IF EXISTS",
    "DROP INDEX code_depends_issue IF EXISTS",
    "DROP INDEX agent_thought IF EXISTS",
]


def run_migration(uri: str, user: str, password: str, rollback: bool = False) -> None:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        with driver.session() as session:
            if rollback:
                logger.info("Running rollback...")
                for query in ROLLBACK_QUERIES:
                    try:
                        session.run(query)
                        logger.info(f"Executed: {query}")
                    except Exception as e:
                        logger.warning(f"Rollback warning: {e}")
                logger.info("Rollback complete")
            else:
                logger.info("Running v0.9.0 schema migration...")
                for name, query in MIGRATION_QUERIES:
                    try:
                        session.run(query)
                        logger.info(f"Created: {name}")
                    except Exception as e:
                        logger.warning(f"Migration warning for {name}: {e}")
                logger.info("Migration complete")
    finally:
        driver.close()


def main():
    parser = argparse.ArgumentParser(description="Neo4j v0.9.0 schema migration")
    parser.add_argument("--uri", default="bolt://localhost:7687", help="Neo4j URI")
    parser.add_argument("--user", default="neo4j", help="Neo4j user")
    parser.add_argument("--password", required=True, help="Neo4j password")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration")
    args = parser.parse_args()
    
    run_migration(args.uri, args.user, args.password, args.rollback)


if __name__ == "__main__":
    main()