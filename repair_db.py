"""
repair_db.py

Cleans up a corrupted django_migrations table before Django's migration
loader runs.

Django's migration loader validates the consistency of applied migrations
BEFORE it will run any new migrations. If the django_migrations table has
out-of-order or otherwise corrupted records (e.g. records for 'admin' or
'auth' applied before their dependencies), Django raises
InconsistentMigrationHistory and refuses to proceed - even a migration
meant to fix the history can't run, because the check happens first.

This script connects directly to Postgres with psycopg2, bypassing Django
entirely, and deletes the corrupted records for the known-problematic apps.
Once the bad rows are gone, `python manage.py migrate` can run normally and
will simply re-apply the missing migrations for those apps.

Intended usage (e.g. as part of a preDeployCommand):

    python repair_db.py && python manage.py migrate

This script is idempotent - if the table is already clean, the DELETE
simply removes zero rows and the script exits successfully.
"""

import os
import sys

import psycopg2

APPS_TO_CLEAN = ("admin", "auth", "contenttypes", "sessions")


def get_connection():
    host = os.environ.get("PGHOST")
    user = os.environ.get("PGUSER")
    password = os.environ.get("PGPASSWORD")
    database = os.environ.get("PGDATABASE")
    port = os.environ.get("PGPORT", "5432")

    return psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=database,
        port=port,
    )


def repair_migration_history():
    conn = None
    try:
        conn = get_connection()
        conn.autocommit = False

        with conn.cursor() as cursor:
            # If the table doesn't exist yet, there's nothing to repair -
            # Django will create it as part of a normal `migrate` run.
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name = 'django_migrations'
                )
                """
            )
            (table_exists,) = cursor.fetchone()

            if not table_exists:
                print("django_migrations table does not exist yet, nothing to repair.")
                return

            cursor.execute(
                "DELETE FROM django_migrations WHERE app IN (%s, %s, %s, %s)",
                APPS_TO_CLEAN,
            )
            deleted = cursor.rowcount

        conn.commit()

        if deleted:
            print(
                f"Removed {deleted} corrupted migration record(s) for "
                f"apps {', '.join(APPS_TO_CLEAN)}."
            )
        else:
            print("django_migrations table already clean, nothing to remove.")

    except Exception as exc:
        if conn is not None:
            conn.rollback()
        print(f"Failed to repair migration history: {exc}", file=sys.stderr)
        raise
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    repair_migration_history()
