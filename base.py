"""Содержит функции и константы"""

# Цвета
COLOR1 = 'White'
COLOR2 = 'Gray'
COLOR3 = '#DEDEDE'
BLACK = 'Black'
RED = "#FF290D"
DEED_COLOR1 = "#FF290D"
DEED_COLOR2 = "#04DBFF"

# Шрифты
COMMON_FONT = ('Arial', 12)
COMMON_FONT_COLOR = 'White'

# Надписи на виджетах
START_TEXT = 'Старт'
STOP_TEXT = 'Приостановить'
CBOX_DEFAULT = 'Выберите дело'
FINISH_DAY_TEXT = 'Завершить день'
CHANGE_PLAN_TEXT = 'Обновить план'
DEFAULT_TIME = '00:00:00'  # Начальный ввод в секундомер

# Сообщения об ошибках
HTTP_ERROR = 'Ошибка при извлечении данных из Google Calendar'
SERVER_NOT_FOUND_ERROR = 'Ошибка при подключении к серверу'

# ключи словаря temp_json
CURRENT_DEED = "current_deed"
TIME_MAIN = "time_main"
TIME_DEED = "time_deed"

# ключи словаря от API
TIME_START = 'time_start'
TIME_END = 'time_end'

# ключи словаря main_json
NAME = "name"
TIME = "time"
PLAN_TIME = "plan_time"
FACT_TIME = "fact_time"

# Прочее
MINS_IN_ROW = 15  # количество минут в одной строчке на панели дня DeedsPanel
DAY_ROWS = 97 #количество строчек на панели дня в DeedsPanel. 1 строчка - 15 мин.
SAVE_CYCLE_TIME = 60 # время между сохранениями в временный JSON (секунды)
READONLY = 'readonly' # константа состояния виджета tkinter

def calculate_time(time1: str, time2: str) -> int:
    """Вычисляет разницу (в секундах) между двумя временными метками в формате hh:mm. time1 < time2.
       Если time 1 > time2 (в случае окончания дела на следующий день) к time2 прибавляется 24 часа.
       Пример: 23:00-03:00 -> 23:00-26:00. Это обеспечивает корректный расчёт длительности дела"""

    times = time1.split(':') + time2.split(':')
    for i, value in enumerate(times):
        times[i] = int(value)

    time2 = times[2] * 3600 + times[3] * 60
    time1 = times[0] * 3600 + times[1] * 60

    if time1 > time2:
        time2 += 24 * 3600 # 24 часа в сутках и 3600 сек. в часе

    return time2 - time1


def time_to_sec(time_f: str) -> int:
    """Переводит время в секунды из формата hh:mm:ss"""
    time_res = time_f.split(':')
    for i, value in enumerate(time_res):  # проверка на незначащие нули
        time_res[i] = rm_insignificant_zeros(time_res[i])

    hours = time_res[0] * 3600
    minutes = time_res[1] * 60
    seconds = time_res[2]

    return hours + minutes + seconds


def time_to_format(time_sec: int) -> str:
    """Переводит время из секунд в формат hh:mm:ss"""
    hours = str(time_sec // 3600).rjust(2, '0')  # Добавление незначащих нулей
    minutes = str((time_sec // 60) % 60).rjust(2, '0')
    seconds = str(time_sec % 60).rjust(2, '0')
    return f'{hours}:{minutes}:{seconds}'


def rm_insignificant_zeros(time_: str) -> int:
    """Удаляет незначащие нули. time_ должно быть в формате  HH ИЛИ MM ИЛИ SS."""
    if time_[0] == '0':
        return int(time_[1])
    else:
        return int(time_)
