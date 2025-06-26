import json
import pathlib
import datetime
from zoneinfo import ZoneInfo

from httplib2 import ServerNotFoundError
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from googleapiclient.discovery import build
from base import (time_to_sec, calculate_time, time_to_format, CURRENT_DEED, TIME, TIME_MAIN, TIME_DEED, PLAN_TIME,
                  FACT_TIME, NAME, CBOX_DEFAULT, TIME_START, TIME_END, HTTP_ERROR, SERVER_NOT_FOUND_ERROR, IGNORING_TIME,
                  TASK_DATA, TIMING_DATA, DEFAULT_TIME)

"""
Структура json'ов: 
   temp_json: {CURRENT_DEED: название дела, 
               TIME_START: время старта (HH:MM:SS),
               TIME_END: время окончания (HH:MM:SS)}
               
   main_json: {FACT_TIME: 
                {<название дела>: {TIME: время (из StopWatchSelector) в секундах}}, 
                PLAN_TIME: 
                {<название дела>:{TIME: время согласно календарю (в секундах), 
                       IGNORING_TIME: игнорируемые отрезки времени в формате HH:MM-HH:MM вида: ['time_start-time_end', ]}}}
"""

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
    day_data: list[dict]

    # Константы для определения положения временной метки по отношению к другой временной метке
    EARLIER = 'earlier'
    LATER = 'later'

    def __init__(self):
        self.api_processor = APIProcessor()
        self.day_data = self.get_plan()
        self.create_jsons()

    def create_jsons(self):

        if not temp_json_path.is_file():
            temp_json_struct = {
                CURRENT_DEED: CBOX_DEFAULT, TIME_MAIN: DEFAULT_TIME, TIME_DEED: DEFAULT_TIME
            }
            with open(temp_json_path, 'w') as temp:
                json.dump(temp_json_struct, temp)

        processed_data = self.process_day_data(self.day_data)

        if not main_json_path.is_file():
            main_json_struct = {
                FACT_TIME: {},  # NAME: {TIME: 'время в секундах'}
                PLAN_TIME: {}
            }
            for deed in processed_data:
                main_json_struct[FACT_TIME][deed[NAME]] = {TIME: '0'}

            for deed in processed_data:
                main_json_struct[PLAN_TIME][deed[NAME]] = {TIME: deed[TIME], IGNORING_TIME: []}

            with open(main_json_path, 'w') as main_:
                json.dump(main_json_struct, main_)

    def save(self, data: dict):
        """Сохраняет данные в temp_json и main_json."""
        deed_name = data[CURRENT_DEED]

        with open(main_json_path, 'rb') as main_:
            main_data = json.load(main_)

        if deed_name not in main_data[FACT_TIME].keys():
            return

        main_data[FACT_TIME][deed_name][TIME] = time_to_sec(data[TIME_DEED])

        with open(main_json_path, 'w') as main_:
            json.dump(main_data, main_)

        with open(temp_json_path, 'w') as temp:
            json.dump({CURRENT_DEED: deed_name, TIME_MAIN: data[TIME_MAIN], TIME_DEED: data[TIME_DEED]}, temp)

    def process_day_data(self, day_data: list[dict]) -> list[dict]:
        """Обрабатывает day_data в пригодный для ввода в main_json формат. Удаляет повторяющиеся дела и суммирует их
           длительность, удаляет дела, начатые ранее 00:00 текущего дня.
           Пример: [{"name": deed1, "time_start": 23:00, "time_end": 03:00}, {"name": deed2, ""}]"""
        # ToDo: желательно отрефакторить, порождает проблемы (убрать вложенную функцию)
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
        deeds = [{NAME: deed[NAME], TIME: calculate_time(deed[TIME_START], deed[TIME_END])} for deed in day_data]

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
        """Записывает в PLAN_TIME изменённый план. Внимание: все IGNORING_TIME при этом удаляются"""

        def check_delete(changed_names: list, last_names: list, deeds: dict):
            """Проверяет новый план на предмет удалённых или добавленных дел, добавляет или удаляет соответствующие дела
               из FACT_TIME."""
            to_delete = []
            to_add = []
            for c_name, l_name in zip(changed_names, last_names):
                if c_name not in last_names:  #  дело добавлено
                    to_add.append(c_name)
                if l_name not in changed_names:  # дело удалено
                    to_delete.append(l_name)

            for key in list(deeds[FACT_TIME].keys()):
                if key in to_delete:
                    deeds[FACT_TIME].pop(key)
                if key in to_add:
                    deeds[FACT_TIME][key] = {TIME: '0'}

            return deeds

        with open(main_json_path, 'rb') as main_:
            deeds_data = json.load(main_)

        changed_data = self.api_processor.get_data()

        deeds_data[PLAN_TIME] = {}
        processed_data = self.process_day_data(changed_data)
        for deed in processed_data:
            deeds_data[PLAN_TIME][deed[NAME]] = {TIME: deed[TIME], IGNORING_TIME: []}

        deeds_data = check_delete([deed[NAME] for deed in changed_data], deeds_data[FACT_TIME].keys(), deeds_data)  #  проверка на добавленные/удалённые дела

        self.day_data = changed_data
        with open(main_json_path, 'w') as main_:
            assert len(deeds_data[FACT_TIME].keys()) == len(deeds_data[PLAN_TIME].keys()), 'Должно быть однинаковое число дел'
            json.dump(deeds_data, main_)

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

        return time_to_format(int(main_data[FACT_TIME][deed_name][TIME]))

    @staticmethod
    def change_ignoring_time(deed_name: str, time_start: str, time_end: str, ignoring: bool):
        """Предназначен для вызова из Deed. Меняет IGNORING_TIME дела deed_name. Если ignoring = True: прибавляет
           разницу между time_end и time_start, если False: отнимает"""
        time_view = f'{time_start}-{time_end}'

        with open(main_json_path, 'rb') as main_:
            deeds_data = json.load(main_)

        deed = deeds_data[PLAN_TIME][deed_name]
        if ignoring:  # Если ignoring - добавить время
            deed[IGNORING_TIME].append(time_view)
        else:
            if time_view in deed[IGNORING_TIME]:
                deed[IGNORING_TIME].remove(time_view)  # На всякий случай, предполагается, что при ignoring = 0 элемент уже есть в списке

        with open(main_json_path, 'w') as main_:
            json.dump(deeds_data, main_)

    @staticmethod
    def get_deed_state(time_start: str, time_end) -> int:
        """Вызывается из Deed при запуске. Возвращает состояние changing_btn в Deed, если f"{time_start}-{time_end}" есть в
           IGNORING_TIME - 1, если нет - 0."""
        time_view = f'{time_start}-{time_end}'

        with open(main_json_path, 'rb') as main_:
            deeds_data = json.load(main_)
        for deed in deeds_data[PLAN_TIME].values():
            if time_view in deed[IGNORING_TIME]:
                return 1
        return 0

    def compare_plans(self) -> bool:
        """Сравнивает план с API и сохранённый план из main_json"""
        api_plan = self.process_day_data(self.get_plan())
        api_data = {}
        for deed in api_plan:
            api_data[deed[NAME]] = {TIME: deed[TIME]}

        with open(main_json_path, 'rb') as main_:
            saved_plan = json.load(main_)

        saved_data = {}  # ToDo: переписать
        for deed_key in saved_plan[PLAN_TIME].keys():
            saved_data[deed_key] = {TIME: saved_plan[PLAN_TIME][deed_key][TIME]}
        return api_data == saved_data

    def get_temp_json(self) -> dict:
        """Возвращает temp_json"""
        with open(temp_json_path, 'rb') as temp:
            return json.load(temp)

    def get_plan(self) -> list[dict]:
        """Получает план из APIProcessor"""
        return self.api_processor.get_data()


class TimingDataHandler:
    """Обрабатывает данные о соответствии плану и возвращает их в GraphicWindow. Структура возвращаемого словаря:
       {TIMING_DATA: [{дата (dd:mm:yy): процент соответствия плану (0-100)}, ...]
        TASK_DATA: {задача: {FACT_TIME: потраченное на задачу время (HH), PLAN_TIME: запланированное время(HH)}, ...}"""

    plan_data: dict[list[dict], list[dict]]
    DAYS_PATH = pathlib.Path(PATH, DAYS)

    def __init__(self, dates: list[str]):
        self.plan_data = {TIMING_DATA: [], TASK_DATA: []}
        for date_ in dates:
            deeds_data = self.process_data(self.take_data(date_))
            if deeds_data:  # Если файл <date>.json существует
                self.plan_data[TIMING_DATA].append(self.calculate_timing(deeds_data, date_))

    def take_data(self, date: str) -> dict | bool:
        """Возвращает данные из main_json'a за день, указанный в date"""
        json_path = pathlib.Path(self.DAYS_PATH, f'{date}.json')
        if not json_path.is_file():  # Проверка на существование файла
            return False
        with open(json_path, 'rb') as main_:
            return json.load(main_)

    def process_data(self, deeds_data: dict) -> dict:
        """Вычитает игнорируемое время (ignoring_time) из запланированного. Удаляет дела, где TIME (в PLAN_TIME) = 0 (чтобы избежать помех в расчётах)
           Возвращает словарь дня с вычтенным игнорированным временем и отсутствующим "ignoring_time"."""
        deleting_keys = []
        for deed_key in deeds_data[PLAN_TIME]:  # Проход по значениям словаря
            deed = deeds_data[PLAN_TIME][deed_key]
            deed[TIME] = str(int(deed[TIME]) - self.process_ignoring_time(deed[IGNORING_TIME]))
            deed.pop(IGNORING_TIME)
            if deed[TIME] == '0':
                deleting_keys.append(deed_key)  # Добавление ключа в удаляемые

        for key in deleting_keys:
            deeds_data[PLAN_TIME].pop(key)
            deeds_data[FACT_TIME].pop(key)

        return deeds_data

    def process_ignoring_time(self, times: list) -> int:
        """Обрабатывает игнорируемое время. Переводит в секунды и складывает значения игнорируемого времени из списка вида:
           ["время_начала(HH:MM)-время_окончания(HH:MM)", ...]"""
        ignoring_time = 0
        for time_ in times:
            spl_time = time_.split('-')
            ignoring_time += calculate_time(spl_time[0], spl_time[1])

        return ignoring_time

    def calculate_timing(self, deeds_data: dict, date_: str) -> dict:
        """Вычисляет соответствие плану. Возвращает словарь для TIMING_DATA вида: {дата (dd:mm:yy): процент соответствия плану (0-100)}"""
        time_sum = 0
        deeds = 0
        for deed_key in deeds_data[FACT_TIME]:  # в main_json дела всегда идут в одном порядке в PLAN- и FACT_TIME
            fact_deed = deeds_data[FACT_TIME][deed_key]  # дело из FACT_TIME
            plan_deed = deeds_data[PLAN_TIME][deed_key]  # соответствующее дело из PLAN_TIME

            fact_deed_time = int(fact_deed[TIME])
            plan_deed_time = int(plan_deed[TIME])
            deeds += 1

            if fact_deed_time >= plan_deed_time and plan_deed_time != 1:  # Если FACT_TIME >= PLAN_TIME - соответствие 100-процентное
                time_sum += 100  # plan_deed_time != 1 нужно для случая с полным игнорированием дела, когда TIME = 0, в этом случае дело не может быть выполнено.
            else:

                time_sum += 100 - (((plan_deed_time - fact_deed_time) / plan_deed_time) * 100)  # Вычисляем соответствие

        time_sum += time_sum // deeds  # Прибавляем среднее арифметическое всех задач (значение общего соблюдения плана)
        deeds += 1  # Количество прибавлений к time_sum увеличилось (прибавили среднее арифметическое)
        return {date_: round(time_sum // deeds, 2)}

    def calculate_task_data(self, deeds_data: list[dict], date_: str) -> dict:
        """Вычисляет время, выделяемое на задачи в течение дня. Проверяет наличие задачи в plan_data[TASK_DATA], если есть -
           добавляет FACT_TIME и PLAN_TIME к соответствующим ключам словаря задачи, если нет - добавляет словарь с FACT_TIME и
           PLAN_TIME"""



