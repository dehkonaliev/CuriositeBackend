from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.loader import MigrationLoader

CORE_APPS = ('auth', 'admin', 'contenttypes', 'sessions')


class Command(BaseCommand):
    help = (
        'Re-insert missing django_migrations rows for the built-in Django apps '
        '(auth, admin, contenttypes, sessions). Run this once if a deploy fails '
        'with InconsistentMigrationHistory after those rows were removed.'
    )

    def handle(self, *args, **options):
        loader = MigrationLoader(connection, ignore_no_migrations=True)
        restored = 0
        with connection.cursor() as cursor:
            for app_label in CORE_APPS:
                for name in loader.disk_migrations.get(app_label, {}):
                    cursor.execute(
                        "INSERT INTO django_migrations (app, name, applied) "
                        "VALUES (%s, %s, now()) "
                        "ON CONFLICT (app, name) DO NOTHING",
                        [app_label, name],
                    )
                    restored += cursor.rowcount
        self.stdout.write(
            self.style.SUCCESS(f'Restored {restored} migration record(s).')
        )
