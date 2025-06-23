from tkinter import Frame, Label, NORMAL, END, W, E, S, N, TOP, DISABLED
from tkinter.ttk import Combobox
from customtkinter import CTkEntry, CTkButton

import time
from threading import Thread

from base import (COLOR1, COLOR3, COMMON_FONT, DAY_ROWS, MINS_IN_ROW, CBOX_DEFAULT, START_TEXT, STOP_TEXT, COMMON_FONT_COLOR, CURRENT_DEED,
                  TIME_MAIN, TIME_DEED, NAME, TIME_START, TIME_END, TIME, READONLY, DEFAULT_TIME, time_to_sec, rm_insignificant_zeros)

class ComboBox(Combobox):
    """Обёртка для CTKCombobox. Обрабатывает список входных значений (values)"""
    def __init__(self, parent, values: tuple, state: str = NORMAL):
        super().__init__(master=parent, state=READONLY)
        self.configure(values=self.process_values(values))

    def process_values(self, values: tuple) -> list:
        """Удаляет из кортежа входящих значений дубликаты элементов. Пример: ("name", "name") -> ["name"] """
        output_values = []
        for value in values:
            if value in output_values:
                continue
            output_values.append(value)

        return output_values


class StopWatchSelector(Frame):

    #Константы события
    START = 'start'   # Отсчёт запущен
    STOP = 'stop'  # Отсчёт остановлен
    DEED_CHANGED = 'deed_changed'  # Дело изменено
    LAUNCH = 'launch'  # Запуск программы

    def __init__(self, parent, values: tuple, deed_request):
        super().__init__(master=parent)
        self.deed_request = deed_request
        self.values = values
        self.data = {
            CURRENT_DEED: '',
            TIME_MAIN: '',
            TIME_DEED: ''
        }

        self.place_widgets()
        self.counting = False  # Идёт ли отсчёт

    def place_widgets(self):

        start_btn_state = NORMAL

        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)

        self.wdg_selector = ComboBox(self, self.values)
        self.wdg_selector.grid(row=0, column=0, columnspan=2, sticky=W + E)
        self.wdg_selector.bind('<<ComboboxSelected>>', self.change_deed)

        self.wdg_main_swatch = CTkEntry(self)
        self.wdg_main_swatch.grid(row=1, column=0, sticky=W + E)
        self.sw_insert(self.wdg_main_swatch, DEFAULT_TIME)

        self.wdg_deed_swatch = CTkEntry(self)
        self.wdg_deed_swatch.grid(row=1, column=1, sticky=W)
        self.sw_insert(self.wdg_deed_swatch, DEFAULT_TIME)

        self.start_btn = CTkButton(self, text=START_TEXT, state=start_btn_state, command=self.start)
        self.start_btn.grid(row=2, column=0)

        self.stop_btn = CTkButton(self, text=STOP_TEXT, state=DISABLED, command=self.stop)
        self.stop_btn.grid(row=2, column=1)

    def start(self):

        if self.wdg_selector.get() == CBOX_DEFAULT:  # На случай включённой кнопки при CBOX_DEFAULT в селекторе
            return

        self.thread_1 = Thread(target=self.count_time, args=[self.wdg_main_swatch], daemon=True)
        self.thread_1.start()
        self.thread_2 = Thread(target=self.count_time, args=[self.wdg_deed_swatch], daemon=True)
        self.thread_2.start()

        self.counting = True  # флаг для цикла отсчёта

        self.change_wdg_state(self.START)

    def stop(self):
        self.change_wdg_state(self.STOP)

        if self.counting:
            self.counting = False

    def get_data(self) -> dict:
        """Возвращает данные о текущем деле в виде: {"name": название, "time": время в секундах}"""
        return {NAME: self.wdg_selector.get(), TIME: self.wdg_main_swatch.get()}

    def sw_insert(self, widget, text: str):
        widget.configure(state=NORMAL)

        widget.delete(0, END)
        widget.insert(0, text)

        widget.configure(state=READONLY)

    def load_deed(self, deed_data: dict):
        """Вводит нужные значения в Combobox и секундомеры при запуске с созданным temp_json"""

        self.wdg_selector.set(deed_data[CURRENT_DEED])
        self.sw_insert(self.wdg_main_swatch, deed_data[TIME_MAIN])
        self.sw_insert(self.wdg_deed_swatch, deed_data[TIME_DEED])
        self.change_wdg_state(self.LAUNCH)  # Изменение состояния

    def change_wdg_state(self, event: str):
        """Меняет состояние wdg_selector, start_btn и stop_btn в зависимости от события"""
        if event == self.START:
            self.wdg_selector.configure(state=DISABLED)
            self.start_btn.configure(state=DISABLED)
            self.stop_btn.configure(state=NORMAL)

        elif event == self.STOP:
            self.wdg_selector.configure(state=READONLY)
            self.start_btn.configure(state=NORMAL)
            self.stop_btn.configure(state=DISABLED)

        elif event == self.LAUNCH:
            if self.wdg_selector.get() == CBOX_DEFAULT:
                self.start_btn.configure(state=DISABLED)

        elif event == self.DEED_CHANGED:
            self.start_btn.configure(state=NORMAL)

    def change_deed(self, _):
        """Вызывается при смене дела в CTkCombobox. Изменяет состояние кнопки start_btn, меняет current_deed, вводит в секундомер дела
           значение из основного JSON'a"""
        deed = self.wdg_selector.get()
        plan_data = self.deed_request(deed)
        self.sw_insert(self.wdg_deed_swatch, plan_data)

        self.change_wdg_state(self.DEED_CHANGED)

    def get_current_data(self) -> dict:
        """Предназначено для вызова из Window. Возвращает словарь с актуальными данными для записи во временный JSON"""
        self.data[CURRENT_DEED] = self.wdg_selector.get()
        self.data[TIME_MAIN] = self.wdg_main_swatch.get()
        self.data[TIME_DEED] = self.wdg_deed_swatch.get()

        return self.data

    def count_time(self, widget):
        secs = time_to_sec(widget.get())
        while self.counting:
            time.sleep(1)
            secs += 1
            minutes = str((secs // 60) % 60).rjust(2, '0')
            hours = str(secs // 3600).rjust(2, '0')

            self.sw_insert(widget, f'{hours}:{minutes}:{str(secs % 60).rjust(2, '0')}')


class DeedsPanel(Frame):
    def __init__(self, parent):
        super().__init__(master=parent, highlightthickness=3, highlightbackground=COLOR3)
        self.place_widgets()
        self.mark_panel()

    def place_widgets(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=4)

        row = 0
        for hour in range(24):
            wdg_hour = Label(self, text=f'{hour}', font=('Verdana', 10))
            wdg_hour.grid(row=row, column=0, rowspan=4, sticky=N + E)
            row += 4

    def mark_panel(self):

        for i in range(DAY_ROWS):
            self.rowconfigure(i, weight=1)
            if i % 4 == 0:
                bg = "Black"
            else:
                bg = COLOR3
            mark = Frame(self, bg=bg)
            mark.grid(row=i, column=1, sticky=W + E)

    def add_deed(self, deeds: tuple[str, str, str], deed_color: str):
        """Добавляет мероприятие на панель. deeds в виде: (name, time_start, time_end) Время в формате: hh:mm. Предполагается, что время в минутах кратно 15-ти,
           т.е.:00:00, 00:15, 00:30, 00:45 и т.д."""
        name = deeds[NAME]
        time_start = deeds[TIME_START].split(':') # "19:00" -> ["19", "00"]
        time_end = deeds[TIME_END].split(':')

        hours_start = rm_insignificant_zeros(time_start[0])
        mins_start = rm_insignificant_zeros(time_start[1])

        hours_end = rm_insignificant_zeros(time_end[0])
        mins_end = rm_insignificant_zeros(time_end[1])

        # Вычисление строки в таблице
        row_start = round((hours_start * 60 + mins_start) / MINS_IN_ROW)  # Находим общее количество минут с 00:00 и
        row_end = round((hours_end * 60 + mins_end) / MINS_IN_ROW)        # делим на 15 (число минут в одной строке)

        if row_start > row_end:  # обработка случая окончания дела на следующий день, пример: 21:00 - 00:15
            row_end = DAY_ROWS

        # Настройка виджета
        deed_frm = Frame(self, bg=deed_color)
        deed_frm.grid(row=row_start, column=1, rowspan=row_end - row_start, sticky=W + E + N + S)

        deed_lbl = Label(deed_frm, text=name, bg=deed_color, fg=COMMON_FONT_COLOR, font=COMMON_FONT)
        deed_lbl.grid(row=0, column=0, columnspan=2)

        deed_wdg_time = Label(deed_frm, text=f'{deeds[TIME_START]} - {deeds[TIME_END]}', bg=deed_color, fg=COMMON_FONT_COLOR, font=COMMON_FONT)
        deed_wdg_time.grid(row=1, column=0)

class Menu(Frame):

    def __init__(self, parent, buttons: tuple): #Параметры кнопок
        super().__init__(master=parent, bg=COLOR3)
        self.buttons = buttons

    def place_widgets(self):
        for row, args in enumerate(self.buttons):
            button = CTkButton(args)
            button.grid(row=row, column=0)


class DialogWindow(Frame):
    def __init__(self, master, text: str, command=None):
        super().__init__(master=master)


    def grid(self):
        pass
    def pack(self):
        pass