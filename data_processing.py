import json
import pathlib
import datetime
from zoneinfo import ZoneInfo

from httplib2 import ServerNotFoundError
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from googleapiclient.discovery import build
from base import (time_to_sec, calculate_time, time_to_format, CURRENT_DEED, TIME, TIME_MAIN, TIME_DEED, PLAN_TIME,
                  FACT_TIME, NAME, CBOX_DEFAULT, TIME_START, TIME_END, HTTP_ERROR, SERVER_NOT_FOUND_ERROR)

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
        time_max = datetime.datetime(year=today.year, month=today.month, day=today.day, hour=23, minute=59, #23:59:00 текущего дня
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
        names = []

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
            print(f"{HTTP_ERROR}: \n{error}")
        except ServerNotFoundError as server_error:
            print(f"{SERVER_NOT_FOUND_ERROR}: \n{server_error}")

class Saver:
    def __init__(self):
        self.api_processor = APIProcessor()
        self.day_data = self.get_plan()
        self.create_jsons()

    def create_jsons(self):

        if not temp_json_path.is_file():
            temp_json_struct = {
                CURRENT_DEED: CBOX_DEFAULT, TIME_MAIN: '00:00:00', TIME_DEED: '00:00:00'
            }
            with open(temp_json_path, 'w') as temp:
                json.dump(temp_json_struct, temp)

        processed_data = self.process_day_data(self.day_data)

        if not main_json_path.is_file():
            main_json_struct = {
                FACT_TIME: [{NAME: deed[NAME], TIME: '0'} for deed in processed_data],
                PLAN_TIME: processed_data
            }
            with open(main_json_path, 'w') as main_:
                json.dump(main_json_struct, main_)

            with open(main_json_path, 'r') as main_:  ###
                print(json.load(main_))  ###

    def save(self, data: dict):
        with open(temp_json_path, 'w') as temp:
            json.dump({CURRENT_DEED: data[CURRENT_DEED], TIME_MAIN: data[TIME_MAIN], TIME_DEED: data[TIME_DEED]}, temp)

        with open(main_json_path, 'rb') as main_:
            main_data = json.load(main_)
            for deed in main_data[FACT_TIME]:
                if deed[NAME] == data[CURRENT_DEED]:
                    deed[TIME] = time_to_sec(data[TIME_DEED])

        with open(main_json_path, 'w') as main_:
            json.dump(main_data, main_)

    def process_day_data(self, day_data: list[dict]) -> list[dict]:
        """Удаляет дела с повторяющимися именами из списка, получаемого от APIProcessor (day_data)
           и суммирует их длительность. Пример: [{"name": "deed1", "time": 3600}, {"name": "deed1", "time": "3600"}] ->
           -> [{"name": "deed1", "time": "7200"}]"""
        names = []
        indexes = []
        deeds = [{NAME: deed[NAME], TIME: calculate_time(deed[TIME_START], deed[TIME_END])} for deed in day_data]

        for idx, deed in enumerate(deeds):
            if deed[NAME] in names:  # У дела повторяющееся имя
                for first_deed in deeds:  # Нахождение первого дела
                    if first_deed[NAME] == deed[NAME]:
                        indexes.append(idx)
                        first_deed[TIME] = str(int(first_deed[TIME]) + int(deed[TIME]))  # Суммирование длительности
                        break
            names.append(deed[NAME])

        return [deed for idx, deed in enumerate(deeds) if not idx in indexes]  # Исключение дела, если его индекс в списке повторяющихся

    def change_plan(self):
        """Анализирует и записывает в main_json изменённый план. Действует так: обращается к API за новым планом, проходит по
           наибольшему из планов, сравнивая их элементы между собой."""
        last_data = self.day_data
        changed_data = self.api_processor.get_data()

        compare_obj = last_data
        if len(changed_data) > len(last_data):
            compare_obj = changed_data

        for deed in compare_obj:
            if

    def finish_day(self):
        """Вызывается из MainWindow для завершения дня"""
        temp_json_path.unlink() # удаляет временный JSON ToDo: проверить работу

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
        api_plan = self.process_day_data(self.get_plan())
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
