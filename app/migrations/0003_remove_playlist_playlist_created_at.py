# Generated by Django 4.2 on 2023-05-17 22:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_alter_playlist_playlist_created_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='playlist',
            name='playlist_created_at',
        ),
    ]
