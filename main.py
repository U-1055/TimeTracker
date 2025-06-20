import time
from tkinter import Frame, Tk, BOTH, W, E, Y, N, S
from customtkinter import CTkButton, CTkComboBox

from widgets import StopWatchSelector, COLOR3, DeedsPanel, Menu, ComboBox
from data_processing import APIProcessor, Saver

class Window:
    def __init__(self):
        PATH = 'data'
        self.saver = Saver()
        self.day_data = self.get_data()
        self.buttons = ((master), (master))

        self.deeds_panel = DeedsPanel(master)
        self.place_widgets()
        for deed in self.day_data:
            self.deeds_panel.add_deed(deed) # self.day_data будет словарём после отработки функции self.get_data()

    def place_widgets(self):
        master.columnconfigure(0, weight=1)
        master.columnconfigure(1, weight=4)
        master.columnconfigure(3, weight=3)

        master.rowconfigure(0, weight=4)
        master.rowconfigure(1, weight=1)

        menu_frame = Menu(master, self.buttons) # меню
        menu_frame.grid(column=0, row=0, sticky=W + E + N + S)

        wdg_frame = Frame(master, bg='Gray') # основная панель
        wdg_frame.grid(row=0, column=1, sticky=W + E + N + S)

        self.wdg_stop_watch = StopWatchSelector(wdg_frame, tuple(deed[0] for deed in self.day_data)) # секундомер
        self.wdg_stop_watch.grid(row=0, column=0, columnspan=2, sticky=W+E)

        # панель с планом
        self.deeds_panel.grid(row=0, column=3, sticky=W + E + N + S)
        test_btn = CTkButton(wdg_frame, command=self.save)
        test_btn.grid(row=1, column=3)

    def save(self):
        self.saver.save(self.wdg_stop_watch.get_current_data())

    def get_data(self) -> tuple[tuple, tuple]:
        return self.saver.get_data()

class GraphicWindow:
    """Окно с графиком"""
    def __init__(self):
        pass



if __name__ == '__main__':

    root = Tk()
    root.title('TimeTracker')
    root.geometry(f'{root.winfo_screenwidth() // 100 * 60}x{root.winfo_screenheight() // 100 * 60}'
                  f'+{root.winfo_screenwidth() // 100 * 20}+{root.winfo_screenheight() // 100 * 20}')

    master = Frame(root)
    master.pack(fill=BOTH, expand=True)

    window = Window()
    root.mainloop()
