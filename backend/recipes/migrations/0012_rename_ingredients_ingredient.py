# Generated by Django 4.2.13 on 2024-06-15 08:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0011_favorite_unique_favorite_recipe_for_user'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Ingredients',
            new_name='Ingredient',
        ),
    ]