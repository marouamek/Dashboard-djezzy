# Generated by Django 5.2.1 on 2025-05-24 18:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Commentaire', '0002_rename_confiance_commentaireclient_score_prediction'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='commentaireclient',
            options={'managed': False},
        ),
    ]
