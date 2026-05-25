from app.db.init_db import init_db
from app.db.session import SessionLocal


def main() -> None:
    with SessionLocal() as db:
        init_db(db, seed=True)


if __name__ == "__main__":
    main()
