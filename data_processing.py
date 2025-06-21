import json
import pathlib
import datetime
from base import time_to_sec, calculate_time, time_to_format, CURRENT_DEED, TIME, TIME_MAIN, TIME_DEED, PLAN_TIME, FACT_TIME, NAME, CBOX_DEFAULT

PATH = 'data'
DAYS = 'days'
NAME_IDX = 0 # Индекс параметра name в основном JSON
TIME_IDX = 1 # Индекс time в основном JSON
TIME_START_IDX = 1
TIME_END_IDX = 2

temp_json = 'temp.json'
main_json = f'{datetime.date.today().strftime('%d.%m.%y')}.json'
temp_json_path = pathlib.Path(PATH, temp_json)
main_json_path = pathlib.Path(PATH, DAYS, main_json)

class APIProcessor:
    def __init__(self):
        pass

    def send_request(self):
        pass

    def get_data(self) -> tuple[tuple, ...]:
        test_dict = (('C', "09:00", "13:00"),
                     ("Проект", "15:00", "00:15"),
                     ("Схемотехника", "17:30", "21:30"),
                     ("Планирование", "21:45", "22:30"))
        return test_dict


class Saver:
    def __init__(self):
        self.api_processor = APIProcessor()
        self.day_data = self.get_plan()

    def create_jsons(self):

        if not temp_json_path.is_file():
            temp_json_struct = {
                "current_deed": CBOX_DEFAULT, "time_main": '00:00:00', "time_deed": '00:00:00'
            }
            with open(temp_json_path, 'w') as temp:
                json.dump(temp_json_struct, temp)

        if not main_json_path.is_file():
            main_json_struct = {
                "fact_time": [{"name": deed[0], "time": "0"} for deed in self.day_data],
                "plan_time": [{"name": deed[0], "time": calculate_time(deed[1], deed[2])} for deed in self.day_data]
            }
            with open(main_json_path, 'w') as main_:
                json.dump(main_json_struct, main_)

            with open(main_json_path, 'r') as main_:  ###
                print(json.load(main_))  ###

    def save(self, data: dict):
        with open(temp_json_path, 'w') as temp:
            json.dump({"current_deed": data["current_deed"], "time_main": data["time_main"], "time_deed": data["time_deed"]}, temp)

        with open(main_json_path, 'rb') as main_:
            main_data = json.load(main_)
            for deed in main_data["fact_time"]:
                if deed["name"] == data["current_deed"]:
                    deed["time"] = time_to_sec(data["time_deed"])

        with open(main_json_path, 'w') as main_:
            json.dump(main_data, main_)

    def change_plan(self):
        pass

    def finish_day(self):
        """Вызывается из MainWindow для завершения дня"""
        temp_json_path.unlink() # удаляет временный JSON

    def in_process(self) -> bool:
        return temp_json_path.is_file()
    @staticmethod
    def get_deed(deed_name: str) -> str:
        """Предназначен для вызова из StopWatchSelector.
           Возвращает время дела."""
        with open(main_json_path, 'rb') as main_:
            main_data = json.load(main_)
        for deed in main_data[FACT_TIME]:
            if deed[NAME] == deed_name:
                return time_to_format(int(deed[TIME]))

    def compare_plans(self) -> bool:
        """Сравнивает план с API и сохранённый план из main_json"""
        api_plan = [{"name": deed[0], "time": calculate_time(deed[1], deed[2])} for deed in self.get_plan()]
        with open(main_json_path, 'rb') as main_:
            saved_plan = json.load(main_)

        return api_plan == saved_plan[PLAN_TIME]

    def get_temp_json(self) -> dict:
        """Возвращает temp_json"""
        with open(temp_json_path, 'rb') as temp:
            return json.load(temp)

    def get_plan(self) -> tuple[tuple, ...]:
        """Получает план из APIProcessor"""
        try:
            return self.api_processor.get_data()
        except ... : #ToDo: добавить конкретную ошибку
            print("Ошибка при получении данных из Google Calendar")
    def get_data(self):
        """Возвращает данные о дне"""
        return self.day_data