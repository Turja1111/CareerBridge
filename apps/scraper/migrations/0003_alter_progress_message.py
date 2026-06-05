from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0002_add_progress_message'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scrapelog',
            name='progress_message',
            field=models.TextField(blank=True, null=True),
        ),
    ]
