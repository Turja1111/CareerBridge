from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='scrapelog',
            name='progress_message',
            field=models.TextField(blank=True),
        ),
    ]
