import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("scraper", "0003_alter_progress_message"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE scraper_userpreference
                    ALTER COLUMN experience_level TYPE varchar(50)[]
                    USING CASE
                        WHEN experience_level IS NULL OR experience_level = ''
                        THEN ARRAY[]::varchar(50)[]
                        ELSE ARRAY[experience_level]::varchar(50)[]
                    END;

                    ALTER TABLE scraper_userpreference
                    ALTER COLUMN experience_level SET DEFAULT ARRAY[]::varchar(50)[];
                    """,
                    reverse_sql="""
                    ALTER TABLE scraper_userpreference
                    ALTER COLUMN experience_level TYPE varchar(50)
                    USING CASE
                        WHEN cardinality(experience_level) > 0
                        THEN experience_level[1]
                        ELSE ''
                    END;

                    ALTER TABLE scraper_userpreference
                    ALTER COLUMN experience_level SET DEFAULT '';
                    """,
                )
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="userpreference",
                    name="experience_level",
                    field=django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=50),
                        blank=True,
                        default=list,
                        help_text='Experience filters, e.g. ["Entry", "Mid", "Internship"]',
                        size=None,
                    ),
                ),
            ],
        ),
    ]
