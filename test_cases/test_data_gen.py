import random
from base import NAME, TIME_START, TIME_END
import csv


class Generator:

    def __init__(self):
        self.names = ['Планирование', 'Проекты', 'C', 'Python', 'Матеша', 'Схемотехника', 'Поход', 'Отдых', 'Учёба', 'Программирование']

    def generate_time(self, min_time: str) -> str:
        """Генерирует временную метку в формате HH:MM, значение которой не может быть менее min_time (HH:MM)"""
        min_hours, min_minutes = min_time.split(':')
        hours = random.randint(int(min_hours), 23)
        minutes = random.randint(int(min_minutes), 23)
        return f'{str(hours).rjust(2, '0')}:{str(minutes).rjust(2, '0')}'

    def generate_api_dict(self, deeds_num: int, file_name: str):
        """
        Генерирует словарь, получаемый от APIProcessor. Записывает словарь в файл с указанным именем
        :param deeds_num: число дел в словаре
        :param file_name:
        """
        time_start = '00:00'
        deeds = []
        for i in range(deeds_num):
            name = self.names[random.randint(0, len(self.names) - 1)]
            time_end = self.generate_time(time_start)
            deeds.append({NAME: name, TIME_START: time_start, TIME_END: time_end})
            self.generate_main_json(i + 1, deeds)
            time_start = time_end
        with open()

    def generate_main_json(self, number: int, api_dict: list):
        """
        Использует Saver для создания main_json
        :param number: номер тестового случая
        :param api_dict: список словарей, получаемый от APIProcessor
        """


if __name__ == '__main__':
    generator = Generator()
    for i in range(1, 10):
        generator.generate_api_dict(6, f'api_dict_{i}.json')

