"""Содержит функции и константы"""

COLOR1 = 'White'
COLOR2 = 'Gray'
COLOR3 = '#DEDEDE'
DEED_COLOR1 = "#FF290D"
DEED_COLOR2 = "#0398EB"

COMMON_FONT = ('Arial', 12)
COMMON_FONT_COLOR = 'White'

START = 'Старт'
STOP = 'Приостановить'
CBOX_DEFAULT = 'Выберите дело'

CURRENT_DEED = "current_deed"
TIME_MAIN = "time_main"
TIME_DEED = "time_deed"
NAME = "name"
TIME = "time"
PLAN_TIME = "plan_time"
FACT_TIME = "fact_time" #ToDo: перенести константы в data_processing

DAY_ROWS = 97 #количество строчек на панели дня в DeedsPanel. 1 строчка - 15 мин.

SAVE_CYCLE_TIME = 60 # время между сохранениями в временный JSON (секунды)


def calculate_time(time1: str, time2: str) -> int:
    """Вычисляет разницу (в секундах) между двумя временными метками в формате hh:mm. time1 < time2"""

    times = time1.split(':') + time2.split(':')
    for i, value in enumerate(times):
        times[i] = int(value)

    time2 = times[2] * 3600 + times[3] * 60
    time1 = times[0] * 3600 + times[1] * 60

    if time1 > time2:
        ...  #ToDo: продумать случай

    return (times[2] * 3600 + times[3] * 60) - (times[0] * 3600 + times[1] * 60)


def time_to_sec(time_f: str) -> int:
    """Переводит время в секунды из формата hh:mm:ss"""
    time_res = time_f.split(':')
    for i, value in enumerate(time_res):  # проверка на незначащие нули
        if value[0] == '0':
            time_res[i] = value[1]
        time_res[i] = int(time_res[i])

    return time_res[0] * 3600 + time_res[1] * 60 + time_res[2]


def time_to_format(time_sec: int) -> str:
    """Переводит время из секунд в формат hh:mm:ss"""
    hours = str(time_sec // 3600).rjust(2, '0')  # Добавление незначащих нулей
    minutes = str((time_sec // 60) % 60).rjust(2, '0')
    seconds = str(time_sec % 60).rjust(2, '0')
    return f'{hours}:{minutes}:{seconds}'

