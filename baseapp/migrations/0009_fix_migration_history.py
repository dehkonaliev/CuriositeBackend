# Manual data migration to fix a corrupted django_migrations table.
#
# In some Railway Postgres deployments, the 'admin.0001_initial' migration
# record ended up marked as applied before its dependency
# 'authentication.0001_initial' (and the other core Django app migrations)
# had run. This puts the django_migrations table into a state that Django's
# migration loader considers inconsistent, raising:
#
#   InconsistentMigrationHistory: Migration admin.0001_initial is applied
#   before its dependency authentication.0001_initial on database
#   'default'.
#
# This migration removes the offending rows for the built-in Django apps
# (admin, auth, contenttypes, sessions) from django_migrations so that the
# next `migrate` run re-applies them fresh, in the correct dependency order.
#
# This is a one-time repair migration. It is safe to run multiple times:
# if the rows have already been removed (or were never corrupted), the
# DELETE simply affects zero rows.

from django.db import migrations


def delete_corrupted_migration_history(apps, schema_editor):
    """Remove out-of-order migration records for core Django apps.

    These apps' tables already exist in the database (they were created
    the first time these migrations ran), so removing the bookkeeping
    rows is safe - Django will simply re-apply the migrations, which are
    idempotent for already-existing tables/columns in this scenario, and
    the loader's dependency consistency check will then pass.
    """
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM django_migrations WHERE app IN "
            "('admin', 'auth', 'contenttypes', 'sessions')"
        )


def noop_reverse(apps, schema_editor):
    """Intentionally a no-op.

    There is no meaningful way (or need) to restore the previously
    corrupted, out-of-order migration history rows.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('baseapp', '0008_alter_mytoken_token'),
    ]

    operations = [
        migrations.RunPython(
            delete_corrupted_migration_history,
            reverse_code=noop_reverse,
        ),
    ]
