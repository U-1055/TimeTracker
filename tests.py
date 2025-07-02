from data_processing import Saver
from base import FACT_TIME, PLAN_TIME

from pathlib import Path
from data_gen_tst import MAIN_JSONS_PATH, API_DICTS, PROCESSED_DATA_PATH
import json
import random
import pytest

TEST_DIR_PATH = Path('test_cases')
INPUT_DATA = 'input'
OUTPUT_DATA = 'output'


class TestSaver:
    """
    Класс, содержащий методы для тестирования класса Saver (из data_processing). Для работы теста требуется сделать пустым
    __init__ Saver'a.
    """
    MAIN_JSON_STRUCT = {FACT_TIME: {},
                        PLAN_TIME: {}}
    def __init__(self):
        self.saver = Saver()

    def test_converting(self):
        """
        Тестирование преобразований по схеме:
        APIProcessor -> Saver.process_data() -> {FACT_TIME: process_to_fact, PLAN_TIME: process_to_plan} -> main_json
        """
        for api_dict in API_DICTS.iterdir():
            path_number = api_dict.name.split('#')[-1].split('.')[0]  # Получение номера тестового случая
            if (self.__check_num_in_dir(path_number, MAIN_JSONS_PATH) and        # Проверка на наличие соответствующих тестовых случаев для main_json и processed_data
                    self.__check_num_in_dir(path_number, PROCESSED_DATA_PATH)):

                api_data = self.__get_test_data(Path(API_DICTS, f'api_dict#{path_number}.json'))   # Получение тестовых данных
                main_json = self.__get_test_data(Path(MAIN_JSONS_PATH, f'main_json#{path_number}.json'))
                processed_data = self.__get_test_data(Path(PROCESSED_DATA_PATH, f'processed_data#{path_number}.json'))

                saver_processed_data = self.saver.process_day_data(api_data)

                assert processed_data == saver_processed_data, (f'Неверная обработка данных от APIProcessor: \n '  # Тест process_data
                                                                f'Данные APIProcessor:\n{api_data}\n'
                                                                f'Ожидаемый результат:\n{processed_data}\n'
                                                                f'Полученный результат:\n{saver_processed_data}')

                saver_main_json = self.MAIN_JSON_STRUCT
                saver_main_json[FACT_TIME] = self.saver.process_to_fact(saver_processed_data)
                saver_main_json[PLAN_TIME] = self.saver.process_to_plan(saver_processed_data)

                assert saver_main_json == main_json, (f'Неверная обработка processed_data:\n'  # Тест обработки в main_json
                                                      f'Processed_data:\n{saver_processed_data}\n'
                                                      f'Ожидаемый результат:\n{main_json}\n'
                                                      f'Полученный результат:\n{saver_main_json}')
                self.saver.day_data = api_data
                saver_created_main_json = self.saver.create_jsons()
                assert saver_created_main_json == saver_main_json == main_json   # Тест создания main_json'a с помощью Saver

    def __get_test_data(self, path: Path) -> list | dict | bool:
        """
        Возвращает тестовые данные из указанного файла в формате json.
        :param: путь к файлу JSON
        """
        with open(path, 'rb') as file:
            return json.load(file)

    def __check_num_in_dir(self, num: str, dir_: Path) -> None | bool:
        """
        Проверяет наличие в директории файла с соответствующим номером.
        Имя файла должно иметь вид <имя теста>#<номер>.<расширение>
        :param num: номер файла
        :param dir_: путь к директории
        :return: None, если переданный путь не является директорией; True, если файл с указанным номером существует;
                 False, если такого файла не существует.
        """
        if not dir_.is_dir():
            return

        for file in dir_.iterdir():
            file_num = file.name.split('#')[-1].split('.')[0]
            if file_num == num:
                return True

        return False

    def test_process_to_fact(self):
        pass

    def test_process_to_plan(self):
        pass


class DataGenerator:
    """Генератор данных. Принимает на вход словарь вида {<ключ>: <допустимые значения>}"""
    def __init__(self, structure: dict):
        pass

test_saver = TestSaver()
test_saver.test_converting()

if __name__ == '__main__':
    pass

