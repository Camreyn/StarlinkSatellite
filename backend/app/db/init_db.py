import json
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import engine
from app.models import Base
from app.services.seed import seed_database

logger = logging.getLogger(__name__)


def init_db(db: Session, seed: bool = True) -> None:
    settings = get_settings()
    sqlite_path = settings.sqlite_path
    if sqlite_path is not None:
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    if seed:
        seed_database(db)


def dump_schema(path: Path) -> None:
    schema = {
        table.name: sorted(column.name for column in table.columns)
        for table in Base.metadata.tables.values()
    }
    path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
