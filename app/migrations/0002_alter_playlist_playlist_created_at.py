# Generated by Django 4.2 on 2023-05-17 22:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='playlist',
            name='playlist_created_at',
            field=models.DateTimeField(null=True),
        ),
    ]
