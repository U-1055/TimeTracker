from tkinter import Frame, Label, NORMAL, END, W, E, S, N, TOP
from tkinter.ttk import Combobox
from customtkinter import CTkEntry, CTkButton

import time
from threading import Thread

from base import (COLOR1, COLOR3, COMMON_FONT, DAY_ROWS, CBOX_DEFAULT, START, STOP, COMMON_FONT_COLOR, CURRENT_DEED,
                  TIME_MAIN, TIME_DEED, time_to_sec) #ToDo: перевести на константы

class ComboBox(Combobox):
    """Обёртка для CTKCombobox. Обрабатывает список входных значений (values)"""
    def __init__(self, parent, values: tuple, command):
        super().__init__(master=parent, state='readonly')
        self.set(CBOX_DEFAULT)
        self.configure(values=self.process_values(values))

    def process_values(self, values: tuple) -> list:
        """Удаляет из кортежа входящих значений дубликаты элементов. Пример: ("name", "name") -> ["name"] """
        output_values = []
        for value in values:
            if value in output_values:
                continue
            output_values.append(value)

        return output_values

    def load(self, current_deed: str, values):
        """"""
        if current_deed in self.cget('values'):
            self.set(current_deed)
        else:
            self.set(CBOX_DEFAULT)

class StopWatchSelector(Frame):
    def __init__(self, parent, values: tuple, deed_request):
        super().__init__(master=parent)
        self.deed_request = deed_request
        self.values = values
        self.data = {
            "current_deed": '',
            "time_main": '',
            "time_deed": ''
        }

        self.place_widgets()
        self.current_deed = self.wdg_selector.get()
        self.counting = False # Идёт ли отсчёт
        self.running = False # Запущен ли поток

    def place_widgets(self):

        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)

        self.wdg_selector = ComboBox(self, self.values, command=lambda a: self.change_deed)  # ToDo: Разобраться с лямбдами
        self.wdg_selector.grid(row=0, column=0, columnspan=2, sticky=W + E)
        self.wdg_selector.bind('<<ComboboxSelected>>', self.change_deed) #ToDo: написать изменение состояния кнопок при выборе CBOX_DEFAULT

        self.wdg_main_swatch = CTkEntry(self)
        self.wdg_main_swatch.grid(row=1, column=0, sticky=W + E)
        self.wdg_main_swatch.insert(0, '00:00:00')
        self.wdg_main_swatch.configure(state='readonly')

        self.wdg_deed_swatch = CTkEntry(self)
        self.wdg_deed_swatch.grid(row=1, column=1, sticky=W)
        self.wdg_deed_swatch.insert(0, '00:00:00')
        self.wdg_deed_swatch.configure(state='readonly')

        start_btn = CTkButton(self, text=START, command=self.start)
        start_btn.grid(row=2, column=0)

        stop_btn = CTkButton(self, text=STOP)
        stop_btn.grid(row=2, column=1)

    def start(self):
        thread_1 = Thread(target=self.count_time, args=[self.wdg_main_swatch])
        thread_1.start()
        thread_2 = Thread(target=self.count_time, args=[self.wdg_deed_swatch])
        thread_2.start()


    def stop(self):
        pass

    def get_data(self) -> dict:
        """Возвращает данные о текущем деле в виде: {"name": название, "time": время в секундах}"""
        return {"name": self.current_deed, "time": self.wdg_main_swatch.get()}

    def sw_insert(self, widget, text: str): #ToDo: перевести все вводы на sw_insert
        widget.configure(state=NORMAL)

        widget.delete(0, END)
        widget.insert(0, text)

        widget.configure(state='readonly')

    def load_deed(self, deed_data: dict):
        """Вводит нужные значения в Combobox и секундомеры при запуске с созданным temp_json"""
        self.wdg_selector.set(deed_data["current_deed"])
        self.sw_insert(self.wdg_main_swatch, deed_data[TIME_MAIN])
        self.sw_insert(self.wdg_deed_swatch, deed_data[TIME_DEED])

    def change_deed(self, event):
        """Вызывается при смене дела в CTkCombobox. Изменяет состояние кнопок, меняет current_deed, вводит в секундомер дела
           значение из основного JSON'a"""
        deed = self.wdg_selector.get()

        if deed == CBOX_DEFAULT:
            self.wdg_main_swatch.configure(state='disable')
            self.wdg_deed_swatch.configure(state='disable')
        else:
            self.wdg_main_swatch.configure(state='normal')
            self.wdg_deed_swatch.configure(state='normal')

        self.current_deed = self.wdg_selector.get()

        plan_data = self.deed_request(deed)

        self.sw_insert(self.wdg_deed_swatch, plan_data)

    def clear_stopwatches(self):
        self.stop()

        self.sw_insert(self.wdg_main_swatch, '00:00:00')
        self.sw_insert(self.wdg_deed_swatch, '00:00:00')

    def get_current_data(self) -> dict:
        """Предназначено для вызова из Window. Возвращает словарь с актуальными данными для записи во временный JSON"""
        self.data['current_deed'] = self.current_deed
        self.data['time_main'] = self.wdg_main_swatch.get()
        self.data['time_deed'] = self.wdg_deed_swatch.get()

        return self.data

    def count_time(self, widget):
        secs = time_to_sec(widget.get())
        while True:
            time.sleep(1)

            secs += 1
            minutes = str((secs // 60) % 60).rjust(2, '0')
            hours = str(secs // 3600).rjust(2, '0')

            widget.configure(state=NORMAL)
            widget.delete(0, END)
            widget.insert(1, f'{hours}:{minutes}:{str(secs % 60).rjust(2, '0')}')
            widget.configure(state='readonly')

    def get_deed(self) -> str:
        return self.wdg_main_swatch.get()

    def get_main(self) -> str:
        return self.wdg_deed_swatch.get()

    def set_main(self, stime: str):
        self.wdg_main_swatch.insert(0, stime)

    def set_deed(self, stime: str):
        self.wdg_deed_swatch.insert(0, stime)


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
            wdg_hour.grid(row=row, column=0, rowspan=4, sticky=E)
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
        name, time_start, time_end = deeds[0], deeds[1], deeds[2]

        #Проверка на 0 перед временем, пример: 19:09 -> 19:9
        hours_start = time_start.split(':')[0]
        mins_start = time_start.split(':')[1]

        hours_end = time_end.split(':')[0]
        mins_end = time_end.split(':')[1]  # ToDo: переписать по возможности, код - кал

        times = [hours_start, mins_start, hours_end, mins_end]

        for i, var in enumerate(times):
            if var[0] == '0':
                times[i] = var[1]
            times[i] = int(times[i]) #Убрать

        # Вычисление строки в таблице
        row_start = round((times[0] * 60 + times[1]) / 15) # По формуле: (hours * 60 + minutes) / minutes_in_row (т.е. 15, т.к. в одной строке 15 мин.)
        row_end = round((times[2] * 60 + times[3]) / 15)

        if row_start > row_end: #обработка случая окончания дела на следующий день, пример: 21:00 - 00:15
            row_end = DAY_ROWS

        # Настройка виджета
        deed_frm = Frame(self, bg=deed_color)
        deed_frm.grid(row=row_start, column=1, rowspan=row_end - row_start, sticky=W + E + N + S)

        deed_lbl = Label(deed_frm, text=name, bg=deed_color, fg=COMMON_FONT_COLOR, font=COMMON_FONT)
        deed_lbl.grid(row=0, column=0, columnspan=2)

        deed_wdg_time = Label(deed_frm, text=f'{time_start}:{time_end}', bg=deed_color, fg=COMMON_FONT_COLOR, font=COMMON_FONT)
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