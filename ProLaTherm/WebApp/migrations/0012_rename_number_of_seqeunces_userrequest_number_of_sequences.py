# Generated by Django 4.2.2 on 2023-07-05 18:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('WebApp', '0011_userrequest_email'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userrequest',
            old_name='number_of_seqeunces',
            new_name='number_of_sequences',
        ),
    ]