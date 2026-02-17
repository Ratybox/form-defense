# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='formentry',
            name='password_hash',
            field=models.CharField(default='', max_length=64),
            preserve_default=False,
        ),
    ]
