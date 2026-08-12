# This migration previously deleted the migration-history bookkeeping rows for
# the built-in Django apps (admin, auth, contenttypes, sessions) to repair a
# corrupted django_migrations table.
#
# That approach was fundamentally broken: on a fresh database those rows are
# legitimately present and needed, so deleting them re-corrupted every new
# deployment, e.g.:
#
#   InconsistentMigrationHistory: Migration authentication.0001_initial is
#   applied before its dependency auth.0012_alter_user_first_name_max_length
#
# This migration is now intentionally a NO-OP. It is kept in place (instead of
# being deleted) so that environments which already recorded this migration
# remain consistent with the on-disk migration graph.

from django.db import migrations


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('baseapp', '0008_alter_mytoken_token'),
    ]

    operations = [
        migrations.RunPython(
            noop,
            reverse_code=noop,
        ),
    ]
