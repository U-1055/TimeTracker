import time
from tkinter import Frame, Tk, BOTH, W, E, N, S
from customtkinter import CTkButton
from threading import Thread

from widgets import StopWatchSelector, DeedsPanel, Menu
from data_processing import Saver
from base import DEED_COLOR1, DEED_COLOR2, SAVE_CYCLE_TIME, NAME


class Window:
    def __init__(self):

        self.saver = Saver()
        self.day_data = self.get_data()
        self.buttons = (master, master)

        self.deeds_panel = DeedsPanel(master)
        self.place_widgets()

        for num, deed in enumerate(self.day_data):
            if num % 2 == 0:
                color = DEED_COLOR2
            else:
                color = DEED_COLOR1

            self.deeds_panel.add_deed(deed, color)  # self.day_data будет словарём после отработки функции self.get_data()

        self.saving_thread = Thread(target=self.saving_cycle, daemon=True)
        self.saving_thread.start()

        if self.saver.in_process():  # Если день не закончен
            if self.saver.compare_plans():
                self.wdg_stop_watch.load_deed(self.saver.get_temp_json())  # Загружает дело из temp_json в StopWatchSelector

    def place_widgets(self):
        master.columnconfigure(0, weight=1)
        master.columnconfigure(1, weight=4)
        master.columnconfigure(3, weight=3)

        master.rowconfigure(0, weight=4)
        master.rowconfigure(1, weight=1)

        menu_frame = Menu(master, self.buttons)  # меню
        menu_frame.grid(column=0, row=0, sticky=W + E + N + S)

        wdg_frame = Frame(master, bg='Gray')  # основная панель
        wdg_frame.grid(row=0, column=1, sticky=W + E + N + S)

        self.wdg_stop_watch = StopWatchSelector(wdg_frame, tuple(deed[NAME] for deed in self.day_data), self.saver.get_deed) # секундомер
        self.wdg_stop_watch.grid(row=0, column=0, columnspan=2, sticky=W+E)

        # панель с планом
        self.deeds_panel.grid(row=0, column=3, sticky=W + E + N + S)
        test_btn = CTkButton(wdg_frame, command=self.save)
        test_btn.grid(row=1, column=3)

    def save(self):
        self.saver.save(self.wdg_stop_watch.get_current_data())

    def get_data(self) -> tuple[tuple, tuple]:
        return self.saver.get_data()

    def finish_day(self):
        """Вызывается при завершении дня"""
        self.saving_thread.join()
        self.save()

    def saving_cycle(self):
        while True:
            time.sleep(SAVE_CYCLE_TIME)
            self.save()

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
