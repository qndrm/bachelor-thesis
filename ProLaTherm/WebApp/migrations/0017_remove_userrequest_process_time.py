# Generated by Django 4.2.2 on 2023-10-01 11:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('WebApp', '0016_alter_userrequest_process_time'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userrequest',
            name='process_time',
        ),
    ]
