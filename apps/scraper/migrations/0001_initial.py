from django.db import migrations, models, connection
from django.db.models import JSONField

# Use JSONField fallback on SQLite to prevent syntax errors
if connection.settings_dict.get('ENGINE', '').endswith('sqlite3'):
    class ArrayField(JSONField):
        def __init__(self, base_field=None, size=None, **kwargs):
            super().__init__(**kwargs)
else:
    from django.contrib.postgres.fields import ArrayField


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LinkedInCredential',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('email', models.EmailField(max_length=255)),
                ('encrypted_password', models.TextField(help_text='AES-encrypted password')),
                ('session_data', models.TextField(blank=True, help_text='JSON browser cookies for session persistence')),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'LinkedIn Credential',
            },
        ),
        migrations.CreateModel(
            name='ScrapeLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('running', 'Running'), ('success', 'Success'), ('failed', 'Failed')], default='running', max_length=20)),
                ('jobs_found', models.IntegerField(default=0)),
                ('jobs_new', models.IntegerField(default=0)),
                ('error_message', models.TextField(blank=True)),
                ('triggered_by', models.CharField(choices=[('schedule', 'Scheduled'), ('manual', 'Manual'), ('startup', 'Startup')], default='manual', max_length=20)),
            ],
            options={
                'ordering': ['-started_at'],
            },
        ),
        migrations.CreateModel(
            name='UserPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('keywords', ArrayField(base_field=models.CharField(max_length=100), blank=True, default=list, help_text='Search keywords, e.g. ["Python Developer", "Django"]', size=None)),
                ('locations', ArrayField(base_field=models.CharField(max_length=100), blank=True, default=list, help_text='Preferred locations, e.g. ["Remote", "Dhaka"]', size=None)),
                ('work_types', ArrayField(base_field=models.CharField(max_length=20), blank=True, default=list, help_text='Work type filters, e.g. ["Remote", "Hybrid"]', size=None)),
                ('experience_level', models.CharField(blank=True, max_length=50)),
            ],
            options={
                'verbose_name': 'User Preference',
            },
        ),
    ]
