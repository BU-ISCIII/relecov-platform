from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sample",
            name="sample_unique_id",
            field=models.CharField(max_length=12, unique=True),
        ),
    ]
