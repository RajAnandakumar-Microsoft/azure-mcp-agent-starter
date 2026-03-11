"""Quick test script for parallel tool execution."""

import logging
import time

from agent_app.tools import list_related_artifacts

# Configure logging to see parallel execution
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Testing parallel execution for list_related_artifacts...")
    logger.info("=" * 70)

    # Test with REQ-001 which has relationships to JAMA, ADO, and IcePanel
    test_artifact_id = "REQ-001"

    logger.info(f"\nQuerying artifact: {test_artifact_id}")
    logger.info("Watch for concurrent fetch messages...\n")

    start_time = time.time()
    result = list_related_artifacts(test_artifact_id)
    elapsed_time = time.time() - start_time

    logger.info("=" * 70)
    logger.info(f"\nResults for {test_artifact_id}:")
    logger.info(f"  - Source artifact: {result.get('source_artifact', {}).get('id')}")
    logger.info(
        f"  - Related artifacts found: {len(result.get('related_artifacts', []))}"
    )

    if "counts" in result:
        logger.info(f"  - JAMA: {result['counts']['jama']}")
        logger.info(f"  - ADO: {result['counts']['ado']}")
        logger.info(f"  - IcePanel: {result['counts']['icepanel']}")

    if result.get("errors"):
        logger.warning(f"  - Errors: {result['errors']}")

    logger.info(f"\n⏱️  Total time: {elapsed_time:.3f}s")
    logger.info("=" * 70)

    # Show a few related artifacts
    if result.get("related_artifacts"):
        logger.info("\nSample related artifacts:")
        for artifact in result["related_artifacts"][:5]:
            logger.info(
                f"  - {artifact.get('id')}: {artifact.get('title')} "
                f"({artifact.get('source_system')})"
            )
