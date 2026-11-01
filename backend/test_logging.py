from backend.observability import (
    configure_logging,
    get_logger,
    log_event,
)

configure_logging()

logger = get_logger("laika.test")

logger.info("Laika logging system initialized.")

log_event(
    logger,
    "rag_retrieval_completed",
    retrieved_chunks=5,
    duration_ms=42.5,
)

logger.warning("This is a test warning.")