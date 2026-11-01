import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from contextvars import ContextVar
from datetime import datetime, timezone
import time
import uuid

request_id_var = ContextVar("request_id", default="system")

class JSONFormatter(logging.Formatter):
    """Format log as structured JSON."""
    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logging": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "system"),
        }

        event_data = getattr(record, "event_data", None)

        if event_data:
            log_data["data"]  = event_data

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT/"logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR/ "laika.log"

def configure_logging():
    """Configure application-wide logging and attach the global request ID factory."""
    root_logger = logging.getLogger()

    if root_logger.handlers:
        return

    root_logger.setLevel(logging.INFO)
    formatter = JSONFormatter()

    # Intercept standard LogRecord creation globally so ALL loggers (including third-party like primp) get request_id
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id_var.get()
        return record

    logging.setLogRecordFactory(record_factory)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

def get_logger(name: str):
    """Return a named application logger."""
    return logging.getLogger(name)

def log_event(logger, event: str, **data):
    """Write a structured application event."""
    logger.info(
        event,
        extra={"event_data": data}
    )


class RequestIDMiddleware:
    """Assign a unique ID to every incoming HTTP request."""

    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger("laika.request")

    async def __call__(self, scope, receive, send):

        # Only process HTTP requests.
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid.uuid4().hex
        token = request_id_var.set(request_id)

        start_time = time.perf_counter()
        status_code = 500

        async def send_with_request_id(message):
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]

                # Add request ID to the response headers.
                headers = list(message.get("headers", []))
                headers.append(
                    (b"x-request-id", request_id.encode("utf-8"))
                )

                message["headers"] = headers

            await send(message)

        try:
            log_event(
                self.logger,
                "request_started",
                method=scope["method"],
                path=scope["path"],
            )

            await self.app(
                scope,
                receive,
                send_with_request_id
            )

        except Exception:
            self.logger.exception("request_failed")
            raise

        finally:
            duration_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2
            )

            log_event(
                self.logger,
                "request_completed",
                method=scope["method"],
                path=scope["path"],
                status_code=status_code,
                duration_ms=duration_ms,
            )

            request_id_var.reset(token)