import json
import pathlib
import datetime
from zoneinfo import ZoneInfo

from httplib2 import ServerNotFoundError
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from googleapiclient.discovery import build
from base import (time_to_sec, calculate_time, time_to_format, CURRENT_DEED, TIME, TIME_MAIN, TIME_DEED, PLAN_TIME,
                  FACT_TIME, NAME, CBOX_DEFAULT, TIME_START, TIME_END, HTTP_ERROR, SERVER_NOT_FOUND_ERROR, IGNORING_TIME)

"""Структура json'ов: 
   temp_json: {CURRENT_DEED: название дела, 
               TIME_START: время старта (HH:MM:SS),
               TIME_END: время окончания (HH:MM:SS)}
               
   main_json: {[FACT_TIME: 
                {NAME: название дела, 
                 TIME: время (из StopWatchSelector) в секундах}, 
                PLAN_TIME: 
                {NAME: ...,
                 TIME: время согласно календарю (в секундах), 
                 IGNORING_TIME: игнорируемые отрезки времени в формате HH:MM-HH:MM вида: ['time_start-time_end', ]}]}"""

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
        """Обрабатывает полученный от API словарь. Удаляет пробелы в начале и в конце name. Возвращает список вида:
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
                {NAME: deed[self.SUMMARY].strip(),  # Удаляет пробелы
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
        """Обрабатывает day_data в пригодный для ввода в main_json формат. Удаляет повторяющиеся дела и суммирует их
           длительность, удаляет дела, начатые ранее 00:00 текущего дня.
           Пример: [{"name": deed1, "time_start": 23:00, "time_end": 03:00}, {"name": deed2, ""}]"""
        # ToDo: желательно отрефакторить, порождает проблемы
        def rm_last_day():
            """Удаляет дела, начатые ранее 00:00 текущего дня"""

            deed = day_data[0]
            next_deed = day_data[1]
            if time_to_sec(deed[TIME_START]) > time_to_sec(next_deed[TIME_START]):
                indexes.append(0)

        names = []
        indexes = []
        rm_last_day()
        day_data = self.rm_deeds(indexes, day_data)
        indexes = []  # Очистить индексы, чтобы не удалить лишнее при втором вызове rm_deeds
        deeds = [{NAME: deed[NAME], TIME: calculate_time(deed[TIME_START], deed[TIME_END]), IGNORING_TIME: []} for deed in day_data]

        for idx, deed in enumerate(deeds):

            if deed[NAME] in names:  # У дела повторяющееся имя
                for first_deed in deeds:  # Нахождение первого дела с этим именем
                    if first_deed[NAME] == deed[NAME]:
                        indexes.append(idx)
                        first_deed[TIME] = str(int(first_deed[TIME]) + int(deed[TIME]))  # Суммирование длительности
                        break
            names.append(deed[NAME])

        return self.rm_deeds(indexes, deeds)  # Исключение дела, если его индекс в списке повторяющихся

    def rm_deeds(self, indexes: list, deeds: list):
        """Возвращает список без элементов под указанными индексами"""
        return [deed for idx, deed in enumerate(deeds) if not idx in indexes]

    def change_plan(self):
        """Анализирует и записывает в main_json изменённый план. Действует так: обращается к API за новым планом, проходит по
           наибольшему из планов, сравнивая их элементы между собой."""
        last_data = self.day_data
        changed_data = self.api_processor.get_data()

        compare_obj = last_data
        if len(changed_data) > len(last_data):
            compare_obj = changed_data

        for deed in compare_obj:
            pass

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

    @staticmethod
    def change_ignoring_time(deed_name: str, time_start: str, time_end: str, ignoring: bool):
        """Предназначен для вызова из Deed. Меняет IGNORING_TIME дела deed_name. Если ignoring = 1: прибавляет
           разницу между time_end и time_start, если 0: отнимает"""
        time_view = f'{time_start}-{time_end}' # ToDo: попробовать избежать хардкода

        with open(main_json_path, 'rb') as main_:
            deeds_data = json.load(main_)

        for deed in deeds_data[PLAN_TIME]:
            if deed[NAME] == deed_name:
                if ignoring:  # Если ignoring - добавить время
                    deed[IGNORING_TIME].append(time_view)
                else:
                    if time_view in deed[IGNORING_TIME]:
                        deed[IGNORING_TIME].remove(time_view) # На всякий случай, предполагается, что при ignoring = 0 элемент уже есть в списке
                break

        with open(main_json_path, 'w') as main_:
            json.dump(deeds_data, main_)

    @staticmethod
    def get_deed_state(time_start: str, time_end) -> int:
        """Вызывается из Deed при запуске. Возвращает состояние changing_btn в Deed, если f"{time_start}-{time_end}" есть в
           IGNORING_TIME - 1, если нет - 0."""
        time_view = f'{time_start}-{time_end}' # ToDo: попробовать избежать хардкода

        with open(main_json_path, 'rb') as main_:
            deeds_data = json.load(main_)
        for deed in deeds_data[PLAN_TIME]:
            if time_view in deed[IGNORING_TIME]:
                return 1
        return 0

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
        return self.api_processor.get_data()


class TimingDataHandler:
    """Обрабатывает данные о соответствии плану и возвращает их в GraphicWindow"""
    timing_data: list[dict]
    DAYS_PATH = pathlib.Path(PATH, DAYS)

    def __init__(self, dates: list[str]):
        self.timing_data = []
        for date in dates:
            deeds_data = self.take_data(date)
            if deeds_data:  # Если файл date.json существует
                self.timing_data.append(self.calculate_timing(deeds_data))

    def take_data(self, date: str) -> list[dict] | bool:
        """Возвращает данные из main_json'a за день, указанный в date"""
        json_path = pathlib.Path(self.DAYS_PATH, f'{date}.json')
        if not json_path.is_file():  # Проверка на существование файла
            return False
        with open(json_path, 'rb') as main_:
            return self.process_data(json.load(main_))

    def process_data(self, deeds_data: list[dict]) -> list[dict]:
        """Вычитает игнорируемое время (ignoring_time) из запланированного. Возвращает словарь дня с вычтенным
           игнорированным временем и отсутствующим "ignoring_time"."""
        return [{NAME: deed[NAME], TIME: int(deed[TIME]) - int(deed[IGNORING_TIME])} for deed in deeds_data]

    def calculate_timing(self, deeds_data: list[dict]) -> dict:
        """Вычисляет соответствие плану."""