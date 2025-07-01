import time
from tkinter import Frame, Button, Tk, BOTH, W, E, N, S, Y
from customtkinter import CTkButton
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from threading import Thread

from widgets import StopWatchSelector, DeedsPanel, Menu, PeriodEntry
from data_processing import Saver, TimingDataHandler
from base import (DEED_COLOR1, DEED_COLOR2, SAVE_CYCLE_TIME, NAME, FINISH_DAY_TEXT, COLOR1, COLOR3, COLOR2,
                  CHANGE_PLAN_TEXT, PERMISSIBLE_PERCENT)
 # ToDo: убрать assert'ы !!!


class Window(Frame):
    """Основное окно. Содержит логику работы программы"""
    def __init__(self, parent):
        super().__init__(master=parent, bg=COLOR2)
        self.saver = Saver()
        self.day_data = self.saver.day_data  # Получение информации о плане

        self.saving = False
        self.place_widgets()  # Размещение виджетов

        self.wdg_stop_watch.load_deed(self.saver.get_temp_json())  # Загрузка данных в StopWatchSelector
        self.load_to_deeds_panel()  # Загрузка данных в DeedsPanel

        self.saving_thread = Thread(target=self.saving_cycle, daemon=True)  # Запуск цикла сохранения
        self.saving_thread.start()

        if self.saver.in_process():  # temp_json существует? (T.е. день идёт?)
            if not self.saver.compare_plans():
                self.change_plan()

    def place_widgets(self):
        self.columnconfigure(0, weight=4)
        self.columnconfigure(1, weight=3)
        self.rowconfigure(0, weight=4)

        wdg_frame = Frame(self, bg=COLOR3)  # основная панель
        wdg_frame.grid(row=0, column=0, sticky=W + E + N + S)

        wdg_frame.columnconfigure(0, weight=3)
        wdg_frame.columnconfigure(1, weight=1)
        wdg_frame.columnconfigure(2, weight=1)
        wdg_frame.rowconfigure(0, weight=2)
        wdg_frame.rowconfigure(1, weight=1)

        finish_btn = CTkButton(wdg_frame, text=FINISH_DAY_TEXT, fg_color=DEED_COLOR1, command=self.finish_day)
        finish_btn.grid(row=1, column=4)

        self.wdg_stop_watch = StopWatchSelector(wdg_frame, self.saver.get_deed) # секундомер
        self.wdg_stop_watch.grid(row=0, column=0, columnspan=2, sticky=W + E + N + S)
        self.wdg_stop_watch.load_deeds(tuple(deed[NAME] for deed in self.day_data))

        # панель с планом
        self.deeds_panel = DeedsPanel(self, self.saver.change_ignoring_time, self.saver.get_deed_state)
        self.deeds_panel.grid(row=0, column=1, sticky=W + E + N + S)

        save_btn = Button(wdg_frame, command=self.save)
        save_btn.grid(row=1, column=2)

        change_btn = CTkButton(wdg_frame, text=CHANGE_PLAN_TEXT, command=self.change_plan)
        change_btn.grid(row=1, column=3)

    def check_changing(self):
        """Вызывается при нажатии на кнопку изменения плана. Проверяет наличие изменения и вызывает change_plan."""
        if self.saver.compare_plans():
            return
        self.change_plan()

    def change_plan(self):
        """Вызывается при изменении плана. Вызывает соответствующие методы у Saver, DeedsPanel и StopWatchSelector.
           Содержит логику изменения плана."""

        self.to_default()
        self.saver.change_plan()
        self.day_data = self.saver.day_data
        self.wdg_stop_watch.load_deed(self.saver.get_temp_json())
        self.wdg_stop_watch.load_deeds(tuple(deed[NAME] for deed in self.day_data))
        self.load_to_deeds_panel()

        self.saving = True

    def to_default(self):
        """Сохраняет план, останавливает цикл сохранения, устанавливает виджеты в состояния по умолчанию. Вызывается при
           изменении плана"""
        self.save()
        self.saving = False
        self.wdg_stop_watch.to_default()
        self.deeds_panel.clear_panel()

    def save(self):
        self.saver.save(self.wdg_stop_watch.get_current_data())

    def finish_day(self):
        """Вызывается при завершении дня"""
        self.saving = False
        self.save()
        self.saver.finish_day()

    def load_to_deeds_panel(self):
        """Загружает дела в DeedsPanel"""

        for num, deed in enumerate(self.day_data):
            if num % 2 == 0:
                color = DEED_COLOR2
            else:
                color = DEED_COLOR1

            self.deeds_panel.add_deed(deed, color)

    def saving_cycle(self):
        """Цикл сохранения. Раз в SAVE_CYCLE_TIME сек. сохраняет данные из StopWatchSelector."""
        while self.saving:
            time.sleep(SAVE_CYCLE_TIME)
            self.save()

    def collapse_window(self):
        """Вызывается при уничтожении виджета через Menu. Останавливает цикл сохранения и сохраняет данные,
           после чего уничтожает виджет."""
        self.saving = False
        self.save()
        self.grid_forget()

    def place_window(self):
        """Вызывается при размещении окна после вызова collapse_window. Запускает saving_cycle и размещает виджет"""
        self.saving = True
        self.grid(row=0, column=1, sticky=W + E + N + S)


class GraphicWindow(Frame):
    """Окно с графиком"""
    _timing_data: list[dict]

    def __init__(self, parent):
        super().__init__(master=parent)
        self._timing_data = [{}]
        self.graph_built = False
        self._place_widgets()

    def _place_widgets(self):
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=8)
        self.columnconfigure(0, weight=6)

        self.wdg_period_selector = PeriodEntry(self)
        self.wdg_period_selector.grid(row=0, column=0, sticky=W)

        graph_build_btn = Button(self, command=self._take_data)
        graph_build_btn.grid(row=0, column=1)

        self.graph_frm = Frame(self, bg=COLOR1)
        self.graph_frm.grid(row=1, column=0, sticky=W + E + N + S, columnspan=2)

    def _take_data(self):
        """Получает данные о соответствии плану и инициирует построение графика. Вызывается при"""
        dates = self.wdg_period_selector.get_dates()
        if dates:
            timing_handler = TimingDataHandler(dates)
            if self.graph_built:
                self._delete_graph()
            self._build_graph(timing_handler.plan_data)

    def _build_graph(self, plan_data: dict):
        """Строит график соответствия плану. Принимает словарь вида {<дата вида dd.mm.yy>: <процент соответствия плану>}."""
        self.graph_built = True
        dates = list(plan_data.keys())
        percents = [(int(accordance)) for accordance in plan_data.values()]

        figure = Figure(figsize=(5, 5))
        plot = figure.add_subplot(111)
        plot.grid()
        plot.axline(xy1=(0, PERMISSIBLE_PERCENT), slope=0, color='r')
        plot.set_ylim(bottom=0, top=100)
        plot.set_yticks((0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100))
        plot.plot(dates, percents, marker='o', linestyle='dashed')

        graph_view = FigureCanvasTkAgg(figure, self.graph_frm)
        graph_view.draw()
        graph_view.get_tk_widget().pack(fill=BOTH, expand=True)

    def _delete_graph(self):
        """Удаляет виджет графика (и все дочерние виджеты graph_frm)."""
        self.graph_built = False
        for widget in self.graph_frm.winfo_children():
            widget.destroy()

    def collapse_window(self):
        self.grid_forget()

    def place_window(self):
        self.grid(row=0, column=1, sticky=W + E + N + S)


class Settings(Frame):
    def __init__(self, parent):
        super().__init__(master=parent)

    def collapse_window(self):
        self.grid_forget()

    def place_window(self):
        self.grid(row=0, column=1, sticky=W + E + N + S)


def launch():

    root = Tk()
    root.title('TimeTracker')
    root.geometry(f'{root.winfo_screenwidth() // 100 * 60}x{root.winfo_screenheight() // 100 * 60}'
                  f'+{root.winfo_screenwidth() // 100 * 20}+{root.winfo_screenheight() // 100 * 20}')

    master = Frame(root, bg=COLOR2)
    master.pack(fill=BOTH, expand=True)

    master.columnconfigure(0, weight=1)
    master.columnconfigure(1, weight=11)
    master.rowconfigure(0, weight=1)

    window = Window(master)
    window.grid(row=0, column=1, sticky=W + E + N + S)
    graphic = GraphicWindow(master)

    menu = Menu(master, window, {'ТМ': window, 'СТ': graphic})
    menu.grid(row=0, column=0, sticky=W + E + N + S)

    root.mainloop()


if __name__ == '__main__':
    launch()
