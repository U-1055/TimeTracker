from tkinter import Frame, Tk, BOTH, N, S, W, E, NORMAL, DISABLED, Label
from customtkinter import CTkComboBox, CTkButton
import json
import datetime
from threading import Thread

class Window:
    def __init__(self):
        PATH = 'data'
        self.place_widgets()

    def place_widgets(self):
        wdg_frame = Frame(master)
        wdg_frame.pack(anchor=W)

        wdg_deeds_today = ComboBox(wdg_frame)
        wdg_deeds_today.grid(row=0, column=0, columnspan=2, sticky=W+E)

        wdg_btn_start = CTkButton(wdg_frame, text='Начать выполнение')
        wdg_btn_start.grid(row=1, column=0)

        wdg_btn_stop = CTkButton(wdg_frame, text='Приостановить выполнение')
        wdg_btn_stop.grid(row=1, column=1)

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
    def __init__(self, master):
        super().__init__(master=master, state='readonly')
        self.configure(values=[])
        self.bind('<Enter>', self.to_adding_mode)

    def to_adding_mode(self, event):

        self.binding = self.bind('<ButtonPress-1>', self.add_value)
        self.bind('<Leave>', self.to_normal_mode)
        self.configure(state=NORMAL)
        self.focus_get()

    def to_normal_mode(self, event):
        self.configure(state='readonly')
        self.unbind(self.binding) # Невозможен случай, при котором binding не будет объявлен к этому моменту
        self.bind('<Enter>', self.to_adding_mode)
    def add_value(self, event):
        value = self.get()
        values = self.cget('values')
        if not (value == '' or value in values):
            values.append(value)
            self.configure(values=values)

class DeedsList(Frame):
    def __init__(self, master):
        super().__init__(master, bg='Gray')
        self.free_row = 1
        self.create_columns()

    def create_columns(self):

        for number, element in enumerate(('Номер', 'Дело', 'Статус', 'Время')):
            column = Label(self, text=f'-      {element}      -')
            column.grid(row=0, column=number)

    def add_deed(self, deed: str, state: str, time: str = '00.00.00'):
        wdg_num = Label(self, text=f'{self.free_row}.')
        wdg_num.grid(row=self.free_row, column=0)

        for num, content in enumerate((deed, state, time)):
            wdg = Label(self, text=content)
            wdg.grid(row=self.free_row, column=num + 1)

if __name__ == '__main__':

    root = Tk()
    root.title('TimeTracker')
    root.geometry(f'{root.winfo_screenwidth() // 100 * 60}x{root.winfo_screenheight() // 100 * 60}'
                  f'+{root.winfo_screenwidth() // 100 * 20}+{root.winfo_screenheight() // 100 * 20}')

    master = Frame(root)
    master.pack(fill=BOTH, expand=True)

    deeds_list = DeedsList(master)
    deeds_list.pack(anchor=E)

    Window()

    root.mainloop()
