from tkinter import Frame, Label, NORMAL, END, W, E, S, N, TOP
from customtkinter import CTkEntry, CTkButton, CTkComboBox

import time
from threading import Thread

#Константы цветов; импортируются в main.py
COLOR1 = 'White'
COLOR2 = 'Gray'
COLOR3 = '#DEDEDE'
COMMON_FONT = ('Arial', 12)


START = 'Старт'
STOP = 'Приостановить'
CBOX_DEFAULT = 'Выберите дело'
class ComboBox(CTkComboBox):
    """Обёртка для CTKCombobox. Обрабатывает список входных значений (values)"""
    def __init__(self, parent, values: tuple):
        super().__init__(master=parent, state='readonly', font=COMMON_FONT, dropdown_font=COMMON_FONT, fg_color=COLOR1)
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

class DeedsList(Frame):
    def __init__(self, parent, bg: str):
        self.bg = bg
        super().__init__(parent, bg=bg)
        self.free_row = 1
        self.create_columns()

    def create_columns(self):

        for number, element in enumerate(('Номер', 'Дело', 'Статус', 'Время')):
            column = Label(self, text=f'{element}', bg=self.bg)
            column.grid(row=0, column=number)

    def add_deed(self, deed: str, state: str, dtime: str = '00.00.00'):
        wdg_num = Label(self, text=f'{self.free_row}.', bg=self.bg)
        wdg_num.grid(row=self.free_row, column=0)

        for num, content in enumerate((deed, state, dtime)):
            wdg = Label(self, text=content, bg=self.bg)
            wdg.grid(row=self.free_row, column=num + 1)

        self.free_row += 1

class StopWatchSelector(Frame):
    def __init__(self, parent, values: tuple):
        super().__init__(master=parent)
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

        self.wdg_selector = ComboBox(self, self.values)
        self.wdg_selector.grid(row=0, column=0, columnspan=2, sticky=W + E)
        self.wdg_selector.bind('<<ComboboxSelected>>', self.change_deed) #ToDo: разобраться с работой бинда

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

    def load(self, data: list[str, str]):
        """Вводит в секундомеры значения из временного JSON'а"""
        self.wdg_main_swatch.delete(0, END)
        self.wdg_main_swatch.insert(0, data[0])

    def get_data(self) -> dict:
        """Возвращает данные о текущем деле в виде: {"name": название, "time": время в секундах}"""
        return {"name": self.current_deed, "time": self.wdg_main_swatch.get()}

    def change_deed(self, event):
        """Вызывается при смене дела в CTkCombobox. Меняет содержимое словаря, который раз в 5 минут запрашивается Window"""
        deed = self.wdg_selector.get()
        if deed == CBOX_DEFAULT:
            self.wdg_main_swatch.configure(state='disable')
            self.wdg_deed_swatch.configure(state='disable')
        else:
            self.wdg_main_swatch.configure(state='normal')
            self.wdg_deed_swatch.configure(state='normal')
            print('A')


    def get_current_data(self) -> dict:
        """Предназначено для вызова из Window. Возвращает словарь с актуальными данными для заноса во временный JSON"""
        self.data['current_deed'] = self.current_deed
        self.data['time_main'] = self.wdg_main_swatch.get()
        self.data['time_deed'] = self.wdg_deed_swatch.get()

        return self.data

    def time_to_sec(self, time_f: str) -> int:
        """Переводит время в секунды из формата hh:mm:ss"""
        time_res = time_f.split(':')
        for i, value in enumerate(time_res): # проверка на незначащие нули
            if value[0] == '0':
                time_res[i] = value[1]
            time_res[i] = int(time_res[i])

        return time_res[0] * 3600 + time_res[1] * 60 + time_res[2]

    def count_time(self, widget):
        secs = self.time_to_sec(widget.get())
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

        for i in range(97):
            self.rowconfigure(i, weight=1)
            if i % 4 == 0:
                bg = "Black"
            else:
                bg = COLOR3
            mark = Frame(self, bg=bg)
            mark.grid(row=i, column=1, sticky=W + E)

    def add_deed(self, deeds: tuple[str, str, str]):
        """Добавляет мероприятие на панель. deeds в виде: (name, time_start, time_end) Время в формате: hh:mm. Предполагается, что время в минутах кратно 15-ти,
           т.е.:00:00, 00:15, 00:30, 00:45 и т.д."""
        name, time_start, time_end = deeds[0], deeds[1], deeds[2]
        wdg_color = '#8288FF'
        wdg_text_color = 'White'

        #Проверка на 0 перед временем, пример: 19:09 -> 19:9
        hours_start = time_start.split(':')[0]
        mins_start = time_start.split(':')[1]

        hours_end = time_end.split(':')[0]
        mins_end = time_end.split(':')[1] #ToDo: переписать по возможности, код - кал

        times = [hours_start, mins_start, hours_end, mins_end]

        for i, var in enumerate(times):
            if var[0] == '0':
                times[i] = var[1]
            times[i] = int(times[i]) #Убрать

        # Вычисление строки в таблице
        row_start = round((times[0] * 60 + times[1]) / 15) # По формуле: (hours * 60 + minutes) / minutes_in_row (т.е. 15, т.к. в одной строке 15 мин.)
        row_end = round((times[2] * 60 + times[3]) / 15)

        # Настройка виджета
        deed_frm = Frame(self, bg=wdg_color)
        deed_frm.grid(row=row_start, column=1, rowspan=row_end - row_start, sticky=W + E + N + S)

        deed_lbl = Label(deed_frm, text=name, bg=wdg_color, fg=wdg_text_color, font=COMMON_FONT)
        deed_lbl.grid(row=0, column=0, columnspan=2)

        deed_wdg_time = Label(deed_frm, text=f'{time_start}:{time_end}', bg=wdg_color, fg=wdg_text_color, font=COMMON_FONT)
        deed_wdg_time.grid(row=1, column=0)

class Menu(Frame):

    def __init__(self, parent, buttons: tuple): #Параметры кнопок
        super().__init__(master=parent, bg=COLOR3)
        self.buttons = buttons

    def place_widgets(self):
        for row, args in enumerate(self.buttons):
            button = CTkButton(args)
            button.grid(row=row, column=0)

