# Generated by Django 4.2.13 on 2024-06-15 08:35

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipes', '0014_rename_recipes_recipe'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Carts',
            new_name='Cart',
        ),
    ]
