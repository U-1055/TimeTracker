"""Может быть в дальнейшем удалён"""
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

