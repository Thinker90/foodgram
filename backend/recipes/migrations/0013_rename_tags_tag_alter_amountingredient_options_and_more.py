# Generated by Django 4.2.13 on 2024-06-15 08:18

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0012_rename_ingredients_ingredient'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Tags',
            new_name='Tag',
        ),
        migrations.AlterModelOptions(
            name='amountingredient',
            options={'verbose_name': 'Кол-во Ингредиентов', 'verbose_name_plural': 'Кол-во Ингредиентов'},
        ),
        migrations.AlterModelOptions(
            name='ingredient',
            options={'ordering': ('name',), 'verbose_name': 'Ингредиент', 'verbose_name_plural': 'Ингредиенты'},
        ),
        migrations.AlterField(
            model_name='amountingredient',
            name='amount',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1, 'Количество Ингредиентов не может быть меньше 1')], verbose_name='Количество'),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='name',
            field=models.CharField(max_length=64, verbose_name='Ингредиент'),
        ),
    ]
