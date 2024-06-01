from csv import DictReader
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from recipes.models import Ingredients

User = get_user_model()


class Command(BaseCommand):
    help = 'Imports data from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_directory', type=str)

    def handle(self, *args, **options):
        csv_directory = options['csv_directory']

        i = 0
        for row in DictReader(open(Path(csv_directory) / 'ingredients.csv',
                                   encoding='utf-8')):
            ingridient = Ingredients(id=i,
                                     name=row['name'],
                                     measurement_unit=row['measurement_unit'])
            ingridient.save()
            i += 1
        self.stdout.write(self.style.SUCCESS('ingredients выполнен успешно'))

        self.stdout.write(self.style.SUCCESS('Импорт данных выполнен!'))
