from tkinter import Frame, Label, NORMAL, END, W, E, S, N, TOP
from customtkinter import CTkEntry, CTkButton, CTkComboBox

import datetime
import time
from threading import Thread

#Константы цветов; импортируются в main.py
COLOR1 = 'White'
COLOR2 = 'Gray'
COLOR3 = '#DEDEDE'
COMMON_FONT = ('Arial', 12)
class ComboBox(CTkComboBox):
    def __init__(self, parent):
        super().__init__(master=parent, state='readonly')
        self.configure(values=[], fg_color=COLOR3)
        self.bind('<Enter>', self.to_adding_mode)
        self.parent = parent
    def to_adding_mode(self, event):

        self.binding = self.bind('<ButtonPress-1>', self.add_value)
        self.bind('<Leave>', self.to_normal_mode)
        self.configure(state=NORMAL, fg_color=COLOR1)
        self.focus_get()

    def to_normal_mode(self, event):
        self.configure(state='readonly', fg_color=COLOR3)
        self.unbind(self.binding)  # Невозможен случай, при котором binding не будет объявлен к этому моменту
        self.bind('<Enter>', self.to_adding_mode)

    def add_value(self, event):
        value = self.get()
        values = self.cget('values')
        if not (value == '' or value in values):
            values.append(value)
            self.configure(values=values)

    def validate(self, string: str):

        if len(string) > 26:
            return False
        else:
            return True

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

class StopWatch(Frame):
    def __init__(self, parent): # Переделать секундомер
        super().__init__(master=parent)

        self.place_widgets()
        self.counting = False # Идёт ли отсчёт
        self.running = False # Запущен ли поток

    def place_widgets(self):

        self.wdg_stopwatch = CTkEntry(self)
        self.wdg_stopwatch.grid(row=0, column=0, sticky=W + E)
        self.wdg_stopwatch.insert(0, '00:00:00')
        self.wdg_stopwatch.configure(state='readonly')

        self.wdg_btn_control = CTkButton(self, text='Начать отсчёт', command=self.start)
        self.wdg_btn_control.grid(row=1, column=0, sticky=W + E)

    def save(self):
        pass

    def load(self):
        pass

    def start(self):
        self.wdg_btn_control.configure(text='Приостановить', command=self.stop)
        self.counting = True

        if not self.running:
            self.running = True
            self.starting_point = datetime.datetime.now() # Точка отсчёта
            thread_count = Thread(target=self.count_time, daemon=True)
            thread_count.start()

    def stop(self):
        self.wdg_btn_control.configure(text='Начать отсчёт', command=self.start)
        self.counting = False
        if self.running:
            self.running = False

    def count_time(self):
        time_data = self.wdg_stopwatch.get().split(':')
        secs, minutes, hours = int(time_data[0]), int(time_data[1]), int(time_data[2].split('.')[0])
        starting_point = datetime.datetime.strptime(f'{hours}:{minutes}:{secs}', '%H:%M:%S')
        while self.counting:

            if secs == 60:
                secs = 0
                minutes += 1
            if minutes == 60:
                minutes = 0
                hours += 1

            time_now = datetime.datetime.time(datetime.datetime.now())
            time_now = str(time_now).split('.')[1]

            self.wdg_stopwatch.configure(state=NORMAL)
            self.wdg_stopwatch.delete(0, END)
            self.wdg_stopwatch.insert(0, str(starting_point - datetime.datetime.strptime(time_now, '%H:%M:%S')))
            self.wdg_stopwatch.configure(state='readonly')

            time.sleep(1)
            secs += 1

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

