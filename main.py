from tkinter import Frame, Tk, BOTH, N, S, W, E, Y, NORMAL, DISABLED, END, Label, Entry
from customtkinter import CTkComboBox, CTkButton, CTkEntry
import json
import datetime
import time
from threading import Thread, Lock

"""Сделать возможность выгрузки данных о дне в виде таблицы csv. Написать виджет таблицы. Реализовать секундомеры. 
Сделать подведение итого по дню"""

class Window:
    def __init__(self):
        PATH = 'data'
        self.place_widgets()

    def place_widgets(self):
        wdg_frame = Frame(master)
        wdg_frame.pack(anchor=W)

        wdg_deeds_today = ComboBox(wdg_frame)
        wdg_deeds_today.grid(row=0, column=0, columnspan=2, sticky=W+E)

        wdg_stop_watch = StopWatch(wdg_frame)
        wdg_stop_watch.grid(row=1, column=0, columnspan=2, sticky=W+E)

    def start_deed(self):
        pass

    def stop_deed(self):
        pass

    def start_break(self):
        pass

    def save(self):
        pass

    def load(self):
        pass

class ComboBox(CTkComboBox):
    def __init__(self, parent):
        super().__init__(master=parent, state='readonly')
        self.configure(values=[], fg_color=COLOR3)
        self.bind('<Enter>', self.to_adding_mode)

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
            deeds_list.add_deed(deed=value, state='state', dtime=str(datetime.time()))
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

if __name__ == '__main__':

    COLOR1 = 'White'
    COLOR2 = 'Gray'
    COLOR3 = '#DEDEDE'

    root = Tk()
    root.title('TimeTracker')
    root.geometry(f'{root.winfo_screenwidth() // 100 * 60}x{root.winfo_screenheight() // 100 * 60}'
                  f'+{root.winfo_screenwidth() // 100 * 20}+{root.winfo_screenheight() // 100 * 20}')

    master = Frame(root)
    master.pack(fill=BOTH, expand=True)

    Window()

    deeds_list = DeedsList(master, COLOR3)
    deeds_list.pack(anchor=E)

    root.mainloop()
