# Generated by Django 4.2.2 on 2023-07-18 14:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WebApp', '0014_alter_userrequest_process_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userrequest',
            name='process_time',
            field=models.IntegerField(default=0),
        ),
    ]
