"""Может быть в дальнейшем удалён"""
import json
import pathlib
import datetime
import time

PATH = 'data'
DAYS = 'days'

temp_json = 'temp.json'
main_json = f'{datetime.date.today().strftime('%d.%m.%y')}.json'
temp_json_path = pathlib.Path(PATH, DAYS, temp_json)
main_json_path = pathlib.Path(PATH, DAYS, main_json)

class APIProcessor:
    def __init__(self):
        pass

    def send_request(self):
        pass

    def get_data(self) -> tuple[tuple, ...]:
        test_dict = (('C', "09:00", "13:00"),
                     ("Проект", "13:15", "17:15"),
                     ("Схемотехника", "17:30", "21:30"),
                     ("Планирование", "21:45", "22:30"))
        return test_dict
class Saver:
    def __init__(self):
        api_processor = APIProcessor()
        try:
            self.day_data = api_processor.get_data()
        except ... : #ToDo: добавить конкретную ошибку
            print("Ошибка при получении данных из Google Calendar")
        self.create_jsons()

    def create_jsons(self):

        if not temp_json_path.is_file():
            temp_json_struct = {
                "current_deed": '', "time_main": ''
            }
            with open(temp_json_path, 'w') as temp:
                json.dump(temp_json_struct, temp)

        if not main_json_path.is_file():
            main_json_struct = {
                "fact_time": [{"name": "", "time": ""} for deed in self.day_data],
                "plan_time": [{"name": deed[0], "time": self.calculate_time(deed[1], deed[2])} for deed in self.day_data]
            }
            with open(main_json_path, 'w') as main_:
                json.dump(main_json_struct, main_)

            with open(main_json_path, 'r') as main_:  ###
                print(json.load(main_))  ###

    def calculate_time(self, time1: str, time2: str) -> int:
        """Вычисляет разницу (в секундах) между двумя временными метками в формате hh:mm. time1 < time2"""

        times = time1.split(':') + time2.split(':')
        for i, value in enumerate(times):
            times[i] = int(value)

        return (times[2] * 3600 + times[3] * 60) - (times[0] * 3600 + times[1] * 60)

    def save(self, data: dict):
        with open(temp_json_path, 'w') as temp:
            json.dump({"current_deed": data["current_deed"], "time_main": data["time_main"]}, temp)
        print(data)

    def load(self):
        pass

    def get_data(self):
        return self.day_data