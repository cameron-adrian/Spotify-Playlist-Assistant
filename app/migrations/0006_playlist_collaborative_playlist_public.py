# Generated by Django 4.2 on 2023-05-18 22:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_alter_playlist_options_remove_playlist_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='playlist',
            name='collaborative',
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name='playlist',
            name='public',
            field=models.BooleanField(null=True),
        ),
    ]
