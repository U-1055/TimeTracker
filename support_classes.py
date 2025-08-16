

class SwitchableWidget:
    """
    Абстрактный класс переключаемого виджета (с методами collapse_window и place_window) для аннотаций типов в Menu
    """
    def __init__(self):
        raise NotImplementedError

    def collapse_window(self):
        raise NotImplementedError

    def place_window(self):
        raise NotImplementedError
