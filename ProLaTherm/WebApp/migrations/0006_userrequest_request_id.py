# Generated by Django 4.2 on 2023-05-25 12:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WebApp', '0005_remove_userrequest_request_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='userrequest',
            name='request_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]