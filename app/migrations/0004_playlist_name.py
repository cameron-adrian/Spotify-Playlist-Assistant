# Generated by Django 4.2 on 2023-05-17 22:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_remove_playlist_playlist_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='playlist',
            name='name',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
