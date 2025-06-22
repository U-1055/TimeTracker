import json
import pathlib
import datetime
from zoneinfo import ZoneInfo

from httplib2 import ServerNotFoundError
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from googleapiclient.discovery import build
from base import (time_to_sec, calculate_time, time_to_format, CURRENT_DEED, TIME, TIME_MAIN, TIME_DEED, PLAN_TIME,
                  FACT_TIME, NAME, CBOX_DEFAULT, TIME_START, TIME_END)

PATH = 'data'
DAYS = 'days'

temp_json = 'temp.json'
main_json = f'{datetime.date.today().strftime('%d.%m.%y')}.json'
temp_json_path = pathlib.Path(PATH, temp_json)
main_json_path = pathlib.Path(PATH, DAYS, main_json)


class APIProcessor:

    # Значения для авторизации в Google Calendar API

    FILE_PATH = r"C:\Users\filat\.credentials.json"
    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    # Значения для получения данных из Google Calendar API

    START_TIME = "startTime"
    TIME_ZONE = "Asia/Novosibirsk"
    CAL_ID = "filatov_truba@mail.ru"

    #Ключи словаря, возвращаемого API

    ITEMS = 'items'
    SUMMARY = 'summary'
    START = 'start'
    END = 'end'
    DATE_TIME = 'dateTime'

    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(self.FILE_PATH, scopes=self.SCOPES)
        self.service = build('calendar', 'v3', credentials=credentials)

    def send_request(self) -> list[dict]:
        """Отправляет запрос к Google Calendar API. Возвращает результат запроса"""
        today = datetime.date.today()
        time_min = datetime.datetime(year=today.year, month=today.month, day=today.day, hour=0, minute=0, # 00:00:00 текущего дня
                                     tzinfo=ZoneInfo(self.TIME_ZONE)).isoformat('T')
        time_max = datetime.datetime(year=today.year, month=today.month, day=today.day, hour=23, minute=0, #23:59:00 текущего дня
                                     tzinfo=ZoneInfo(self.TIME_ZONE)).isoformat('T')

        day_data = self.service.events().list(calendarId=self.CAL_ID, timeMin=time_min, timeMax=time_max, orderBy=self.START_TIME, singleEvents=True).execute()
        return self.process(day_data)

    def process(self, data_: dict) -> list[dict]:
        """Обрабатывает полученный от API словарь. Возвращает список вида:
        [{"name": название дела, "time_start": время начала в HH:MM, "time_end": время окончания в HH:MM}, ...]"""
        def date_to_time(date_: str) -> str:
            """Принимает дату в виде yy-mm-ddTHH:MM:SS+-HH:MM:SS. Возвращает время в формате HH:MM"""
            time_ = date_.split('T')[1]
            time_ = time_.split('+')[0]  #  Рассматривается конкретный часовой пояс, так что может быть только +; - и Z быть не может
            time_ = time_[::-1].split(':', 1)[1]

            return time_[::-1]

        plan_struct = []
        for num, deed in enumerate(data_[self.ITEMS]):
            plan_struct.append(
                {NAME: deed[self.SUMMARY],
                 TIME_START: date_to_time(deed[self.START][self.DATE_TIME]),
                 TIME_END: date_to_time(deed[self.END][self.DATE_TIME])})

        return plan_struct

    def get_data(self) -> list[dict]:
        try:
            return self.send_request()
        except HttpError as error:
            print(f"Ошибка при извлечении данных из календаря:{error}")
        except ServerNotFoundError as server_error:
            print(f"Сервер не найден: {server_error}")

class Saver:
    def __init__(self):
        self.api_processor = APIProcessor()
        self.day_data = self.get_plan()
        self.create_jsons()

    def create_jsons(self):

        if not temp_json_path.is_file():
            temp_json_struct = {
                "current_deed": CBOX_DEFAULT, "time_main": '00:00:00', "time_deed": '00:00:00'
            }
            with open(temp_json_path, 'w') as temp:
                json.dump(temp_json_struct, temp)

        if not main_json_path.is_file():
            main_json_struct = {
                "fact_time": [{"name": deed[NAME], "time": "0"} for deed in self.day_data],
                "plan_time": [{"name": deed[NAME], "time": calculate_time(deed[TIME_START], deed[TIME_END])} for deed in self.day_data]
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
        api_plan = [{"name": deed[NAME], "time": calculate_time(deed[TIME_START], deed[TIME_END])} for deed in self.get_plan()]
        with open(main_json_path, 'rb') as main_:
            saved_plan = json.load(main_)

        return api_plan == saved_plan[PLAN_TIME]

    def get_temp_json(self) -> dict:
        """Возвращает temp_json"""
        with open(temp_json_path, 'rb') as temp:
            return json.load(temp)

    def get_plan(self) -> list[dict]:
        """Получает план из APIProcessor"""
        try:
            return self.api_processor.get_data()
        except HttpError as err:
            print(err)

    def get_data(self):
        """Возвращает данные о дне"""
        return self.day_data