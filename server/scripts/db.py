import os

import typer
from alembic.command import upgrade as alembic_upgrade
from alembic.config import Config
from sqlalchemy_utils import create_database, database_exists, drop_database

from polar.config import settings

cli = typer.Typer()


def seed_issues() -> None:
    # Keeping this as a no-op if we decide to use it
    ...


def get_sync_postgres_dsn() -> str:
    # TODO: Dirty and quick hack. Change this later to drop unnecessary dependency.
    async_dsn = str(settings.postgres_dsn)
    return async_dsn.replace("asyncpg", "psycopg2")


def _upgrade(revision: str = "head") -> None:
    config_file = os.path.join(os.path.dirname(__file__), "../alembic.ini")
    config = Config(config_file)
    config.set_main_option("sqlalchemy.url", get_sync_postgres_dsn())
    alembic_upgrade(config, revision)


def _recreate() -> None:
    if database_exists(get_sync_postgres_dsn()):
        drop_database(get_sync_postgres_dsn())

    create_database(get_sync_postgres_dsn())
    _upgrade("head")


@cli.command()
def upgrade(
    revision: str = typer.Option("head", help="Which revision to upgrade to")
) -> None:
    _upgrade(revision)


@cli.command()
def recreate() -> None:
    _recreate()


@cli.command()
def seed() -> None:
    seed_issues()


if __name__ == "__main__":
    if not settings.is_development() or settings.is_testing():
        raise RuntimeError("DANGER! You cannot run this script in {settings.env}!")

    cli()