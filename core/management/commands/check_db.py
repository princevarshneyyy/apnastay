from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = "Check database connection and verify whether PostgreSQL or SQLite is active."

    def handle(self, *args, **options):
        db_settings = settings.DATABASES['default']
        engine = db_settings.get('ENGINE', '')

        self.stdout.write(self.style.NOTICE(f"[ApnaStay] Testing database connection..."))
        self.stdout.write(f"Configured Engine: {engine}")
        self.stdout.write(f"Database Name: {db_settings.get('NAME')}")

        try:
            with connection.cursor() as cursor:
                if 'postgresql' in engine:
                    cursor.execute("SELECT version();")
                    row = cursor.fetchone()
                    self.stdout.write(self.style.SUCCESS(f" SUCCESS: Connected to PostgreSQL!"))
                    self.stdout.write(f"PostgreSQL Version: {row[0]}")
                elif 'sqlite' in engine:
                    cursor.execute("SELECT sqlite_version();")
                    row = cursor.fetchone()
                    self.stdout.write(self.style.SUCCESS(f" SUCCESS: Connected to SQLite database!"))
                    self.stdout.write(f"SQLite Version: {row[0]}")
                else:
                    self.stdout.write(self.style.SUCCESS(f" SUCCESS: Connected to database!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f" FAILED to connect to database: {str(e)}"))
