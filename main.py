import time
import tkinter
from tkinter import Frame, Canvas, LabelFrame, Tk, Entry, Label, BOTH, W, E, N, S
from tkinter.messagebox import showerror

from customtkinter import CTkButton, CTkFrame
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from googleapiclient.errors import HttpError

from widgets import StopWatchSelector, DeedsPanel, Menu, PeriodEntry, ColorFrame, ComboBoxAdd, DialogWindow
from data_processing import Saver, TimingDataHandler
from base import (DEED_COLOR1, DEED_COLOR2, SAVE_CYCLE_TIME, NAME, FINISH_DAY_TEXT, FRM_COL1, FRM_COL2, BTN_COL,
                  CHANGE_PLAN_TEXT, PERMISSIBLE_PERCENT, LBL_PERIOD_SELECT_TEXT, RED, SAVE_TEXT, TEXT_COL, WARNING_COL, BTN_HOV_COL)


class Window(Frame):
    """Основное окно. Содержит логику работы программы"""

    def __init__(self, parent: tkinter.Widget, bg):
        super().__init__(master=parent, bg=bg)
        try:
            self.saver = Saver()
        except HttpError:
            self.day_data = []
            self.saving = False
            showerror('Ошибка при обращении к календарю', 'Возможно, вы указали неверный идентификатор календаря. Перейдите в настройки и измените его')
            return

        self.day_data = self.saver.day_data  # Получение информации о плане

        self.place_widgets()  # Размещение виджетов

        self.saving = True
        self.saving_cycle()

        self.wdg_stop_watch.load_deed(self.saver.get_temp_json())  # Загрузка данных в StopWatchSelector
        self.load_to_deeds_panel()  # Загрузка данных в DeedsPanel

        if self.saver.in_process():  # temp_json существует? (T.е. день идёт?)
            if not self.saver.compare_plans():
                self.change_plan()

    def place_widgets(self):

        self.columnconfigure(0, weight=4)
        self.columnconfigure(1, weight=3)
        self.rowconfigure(0, weight=4)

        wdg_frame = Canvas(self)  # основная панель
        wdg_frame.grid(row=0, column=0, sticky=W + E + N + S)

        wdg_frame.columnconfigure(0, weight=3)
        wdg_frame.columnconfigure(1, weight=1)
        wdg_frame.columnconfigure(2, weight=1)
        wdg_frame.rowconfigure(0, weight=1)

        finish_btn = CTkButton(wdg_frame, text=FINISH_DAY_TEXT, fg_color=RED, text_color=TEXT_COL, command=self.finish_day)
        finish_btn.grid(row=2, column=4)

        self.wdg_stop_watch = StopWatchSelector(wdg_frame, self.saver.get_deed)  # секундомер
        self.wdg_stop_watch.grid(row=0, column=0, columnspan=2, sticky=W + E + N)
        self.wdg_stop_watch.load_deeds(tuple(deed[NAME] for deed in self.day_data))

        # панель с планом
        self.deeds_panel = DeedsPanel(self, self.saver.change_ignoring_time, self.saver.get_deed_state)
        self.deeds_panel.grid(row=0, column=1, sticky=W + E + N + S)

        save_btn = CTkButton(wdg_frame, text=SAVE_TEXT, fg_color=BTN_COL, command=self.save)
        save_btn.grid(row=0, column=2, sticky=N)

        change_btn = CTkButton(wdg_frame, text=CHANGE_PLAN_TEXT, fg_color=BTN_COL, command=self.change_plan)
        change_btn.grid(row=2, column=3)

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

        self._start_saving()

    def to_default(self):
        """Сохраняет план, останавливает цикл сохранения, устанавливает виджеты в состояния по умолчанию. Вызывается при
           изменении плана"""
        self.save()
        self._stop_saving()
        self.wdg_stop_watch.to_default()
        self.deeds_panel.clear_panel()

    def save(self):
        self.saver.save(self.wdg_stop_watch.get_current_data())

    def finish_day(self):
        """Вызывается при завершении дня"""
        self._stop_saving()
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
        if not self.saving:
            return

        self.save()
        self.after(SAVE_CYCLE_TIME * 1000, self.saving_cycle)

    def _start_saving(self):
        self.saving = True
        self.saving_cycle()

    def _stop_saving(self):
        self.saving = False

    def collapse_window(self):
        """Вызывается при уничтожении виджета через Menu. Останавливает цикл сохранения и сохраняет данные,
           после чего уничтожает виджет."""
        if self.saving:
            self.saving = False
            self.save()
        self.grid_forget()

    def place_window(self):
        """Вызывается при размещении окна после вызова collapse_window. Запускает saving_cycle и размещает виджет"""
        self.saving = True
        self.grid(row=0, column=1, sticky=W + E + N + S)


class GraphWindow(Frame):
    """Окно с графиком"""
    _timing_data: list[dict]

    def __init__(self, parent):
        super().__init__(master=parent)
        self._timing_data = [{}]
        self.graph_built = False
        self._place_widgets()

    def _place_widgets(self):
        self.rowconfigure(1, weight=8)
        self.columnconfigure(1, weight=1)

        lbl_period = Label(self, text=LBL_PERIOD_SELECT_TEXT)
        lbl_period.grid(row=0, column=0, sticky=W)

        self.wdg_period_selector = PeriodEntry(self)
        self.wdg_period_selector.grid(row=0, column=1, sticky=W)

        graph_build_btn = CTkButton(self, text='Построить график', command=self._take_data)
        graph_build_btn.grid(row=0, column=2, sticky=W)

        self.graph_frm = Frame(self, bg=FRM_COL1)
        self.graph_frm.grid(row=1, column=0, sticky=W + E + N + S, columnspan=3)

    def _take_data(self):
        """Получает данные о соответствии плану и инициирует построение графика"""
        dates = self.wdg_period_selector.get_dates()
        if dates:
            timing_handler = TimingDataHandler(dates)
            if self.graph_built:
                self._delete_graph()
            self._build_graph(timing_handler.plan_data)

    def _build_graph(self, plan_data: dict):
        """
        Строит график соответствия плану.
        :param plan_data: словарь вида {<дата вида dd.mm.yy>: <процент соответствия плану>}.
        """
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
        """Удаляет виджет графика (и все другие дочерние виджеты graph_frm)."""
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
        self.settings = {}
        self._themes = {"dark_theme": {"frm_col1": '#262626'}}
        self._place_widgets()

    def _place_widgets(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        frm_color = LabelFrame(self, bg=FRM_COL2, text='Внешний вид')
        frm_color.grid(row=0, column=0)

        frm_ignore_deeds = LabelFrame(self, bg=FRM_COL2, text='Игнорируемые дела')
        frm_ignore_deeds.grid(row=0, column=1)

        wdg_ignore_deeds = ComboBoxAdd(frm_ignore_deeds, bg=BTN_COL, save_func=Saver.add_ignore_deed, del_func=Saver.del_ignore_deed, values=Saver.get_ignoring_deeds())
        wdg_ignore_deeds.grid(row=0, column=0, sticky=W + E)

        frm_other_settings = LabelFrame(self, bg=FRM_COL2, highlightthickness=0, text='Другое')
        frm_other_settings.grid(row=0, column=2)

        wdg_calendar_id = Entry(frm_other_settings, bg=BTN_COL, fg=TEXT_COL)
        wdg_calendar_id.grid(row=0, column=0)
        wdg_calendar_id.insert(0, Saver.get_calendar_id())

    def collapse_window(self):
        self.grid_forget()

    def place_window(self):
        self.grid(row=0, column=1, sticky=W + E + N + S)


def launch():

    root = Tk()
    root.title('TimeTracker')
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    root.geometry(f'{screen_width // 100 * 60}x{screen_height // 100 * 60}'
                  f'+{screen_width // 100 * 20}+{screen_height // 100 * 20}')
    root.minsize(width=screen_width // 2, height=screen_height // 2)
    master = Frame(root, bg=FRM_COL1)
    master.pack(fill=BOTH, expand=True)

    master.columnconfigure(1, weight=15)
    master.rowconfigure(0, weight=1)

    window = Window(master, FRM_COL2)
    window.grid(row=0, column=1, sticky=W + E + N + S)

    graph = GraphWindow(master)
    settings = Settings(master)

    menu = Menu(master, window, {'ЧАСЫ': window, 'СТАТ': graph, 'НАСТР': settings}, FRM_COL2, BTN_COL)
    menu.grid(row=0, column=0, sticky=W + E + N + S)

    root.iconbitmap('icons\\logo.ico')
    root.mainloop()


if __name__ == '__main__':
    launch()
