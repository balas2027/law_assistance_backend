import logging
import time

import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

logger = logging.getLogger(__name__)

IS_SQLITE = settings.DATABASE_URL.startswith("sqlite")

_connect_timeout = 10
_retry_delays = (1, 2, 4)


def _connect_with_retry():
    if IS_SQLITE:
        import sqlite3

        return sqlite3.connect(settings.DATABASE_URL.replace("sqlite:///", ""), check_same_thread=False)

    last_error = None
    for attempt, delay in enumerate(_retry_delays, start=1):
        try:
            return psycopg2.connect(
                settings.DATABASE_URL,
                connect_timeout=_connect_timeout,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5,
            )
        except Exception as exc:  # noqa: BLE001 - retry any transient connect failure (DNS, network)
            last_error = exc
            logger.warning("DB connect attempt %d/%d failed: %s", attempt, len(_retry_delays), exc)
            if attempt < len(_retry_delays):
                time.sleep(delay)
    raise last_error


engine_kwargs = {}
if IS_SQLITE:
    engine_kwargs.update({"connect_args": {"check_same_thread": False}})
else:
    engine_kwargs.update(
        {
            "creator": _connect_with_retry,
            "pool_pre_ping": True,
            "pool_recycle": 300,
        }
    )

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()
