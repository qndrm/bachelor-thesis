# Generated by Django 4.2 on 2023-05-25 12:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('WebApp', '0004_userrequest_request_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userrequest',
            name='request_id',
        ),
    ]
