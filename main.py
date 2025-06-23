import time
from tkinter import Frame, Button, Tk, BOTH, W, E, N, S
from customtkinter import CTkButton
from threading import Thread

from widgets import StopWatchSelector, DeedsPanel, Menu
from data_processing import Saver
from base import DEED_COLOR1, DEED_COLOR2, SAVE_CYCLE_TIME, NAME, FINISH_DAY_TEXT, COLOR1, COLOR3, COLOR2, CHANGE_PLAN_TEXT


class Window:
    def __init__(self):

        self.saver = Saver()
        self.day_data = self.saver.day_data

        self.saving = True
        self.deeds_panel = DeedsPanel(master)
        self.place_widgets()

        self.load_to_deeds_panel()

        self.saving_thread = Thread(target=self.saving_cycle, daemon=True)
        self.saving_thread.start()

        if self.saver.in_process():  # Если день не закончен
            self.wdg_stop_watch.load_deed(self.saver.get_temp_json())  # Загружает дело из temp_json в StopWatchSelector

    def place_widgets(self):
        master.columnconfigure(0, weight=1)
        master.columnconfigure(1, weight=4)
        master.columnconfigure(3, weight=3)

        master.rowconfigure(0, weight=4)
        master.rowconfigure(1, weight=1)

        wdg_frame = Frame(master, bg=COLOR3)  # основная панель
        wdg_frame.grid(row=0, column=1, sticky=W + E + N + S)

        self.finish_btn = CTkButton(wdg_frame, text=FINISH_DAY_TEXT, fg_color=DEED_COLOR1, command=self.finish_day)
        self.finish_btn.grid(row=4, column=4)

        self.wdg_stop_watch = StopWatchSelector(wdg_frame, tuple(deed[NAME] for deed in self.day_data), self.saver.get_deed) # секундомер
        self.wdg_stop_watch.grid(row=0, column=0, columnspan=2, sticky=W+E)

        # панель с планом
        self.deeds_panel.grid(row=0, column=3, sticky=W + E + N + S)

        save_btn = CTkButton(wdg_frame, command=self.save)
        save_btn.grid(row=1, column=3)

        change_btn = CTkButton(wdg_frame, text=CHANGE_PLAN_TEXT, command=self.change_plan)

    def change_plan(self):
        """Вызывается при изменении плана. Вызывает соответствующие методы у Saver, DeedsPanel и StopWatchSelector"""
        if self.saver.compare_plans():  # План изменён?
            return
        self.save()  # Сохраняет текущий план
        self.saver.change_plan()  # Запускает изменение плана
        self.day_data = self.saver.day_data
        self.wdg_stop_watch.load_deed(self.saver.get_temp_json())



    def save(self):
        self.saver.save(self.wdg_stop_watch.get_current_data())

    def finish_day(self):
        """Вызывается при завершении дня"""
        self.saving = False
        self.saver.finish_day()
        self.save()

    def load_to_deeds_panel(self):
        for num, deed in enumerate(self.day_data):
            if num % 2 == 0:
                color = DEED_COLOR2
            else:
                color = DEED_COLOR1

            self.deeds_panel.add_deed(deed, color)

    def saving_cycle(self):
        while self.saving:
            time.sleep(SAVE_CYCLE_TIME)
            self.save()


class GraphicWindow(Frame):
    """Окно с графиком"""
    def __init__(self, parent):
        super().__init__(master=parent)

    def grid(self):
        pass

    def pack(self):
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
