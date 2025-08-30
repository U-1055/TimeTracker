import time
import tkinter
from tkinter import Frame, Canvas, LabelFrame, Tk, Entry, Label, BOTH, W, E, N, S, CENTER, END
from tkinter.messagebox import showerror
import typing as tp
from tkinter.ttk import Treeview

from customtkinter import CTkButton, CTkSwitch
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from googleapiclient.errors import HttpError

from widgets import StopWatchSelector, DeedsPanel, Menu, PeriodCalendar, ComboBoxAdd, DialogInput, AllowingEntry, FormWidget
from data_processing import Saver, TimingDataHandler
import base as const
from support_classes import SwitchableWidget


class Window(Frame, SwitchableWidget):
    """Основное окно. Содержит логику работы программы"""
    saver: Saver

    def __init__(self, parent: tkinter.Widget, bg: str, saver: type, restart_func: tp.Callable):
        super().__init__(master=parent, bg=bg)
        self._restart_func = restart_func
        try:
            self.saver = saver()
        except HttpError:
            self.saver = saver
            self.day_data = []
            self.saving = False
            dialog_input = DialogInput(self, title=const.CAL_ID_ERR_TITLE, message=const.CAL_ID_ERR_MSG, label=const.CAL_ID_ERR_LBL,
                        default_text=saver.get_calendar_id(), confirm_command=self._restart)
            dialog_input.grid()

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

        wdg_frame = Frame(self)  # основная панель
        wdg_frame.grid(row=0, column=0, sticky=W + E + N + S)

        wdg_frame.columnconfigure(0, weight=3)
        wdg_frame.columnconfigure(1, weight=1)
        wdg_frame.columnconfigure(2, weight=1)
        wdg_frame.rowconfigure(0, weight=1)

        finish_btn = CTkButton(wdg_frame, text=const.FINISH_DAY_TEXT, fg_color=const.RED, text_color=const.TEXT_COL, hover=False, command=self.finish_day)
        finish_btn.grid(row=2, column=4)

        self.wdg_stop_watch = StopWatchSelector(wdg_frame, self.saver.get_deed)  # секундомер
        self.wdg_stop_watch.grid(row=0, column=0, columnspan=2, sticky=W + E + N)
        self.wdg_stop_watch.load_deeds(tuple(deed[const.NAME] for deed in self.day_data))

        # панель с планом
        self.deeds_panel = DeedsPanel(self, self.saver.change_ignoring_time, self.saver.get_deed_state)
        self.deeds_panel.grid(row=0, column=1, sticky=W + E + N + S)

        save_btn = CTkButton(wdg_frame, text=const.SAVE_TEXT, fg_color=const.BTN_COL, text_color=const.TEXT_COL, hover_color=const.BTN_HOV_COL, command=self.save)
        save_btn.grid(row=0, column=2, sticky=N)

        change_btn = CTkButton(wdg_frame, text=const.CHANGE_PLAN_TEXT, fg_color=const.BTN_COL, text_color=const.TEXT_COL, hover_color=const.BTN_HOV_COL, command=self.change_plan)
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
        self.wdg_stop_watch.load_deeds(tuple(deed[const.NAME] for deed in self.day_data))
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
                color = const.DEED_COLOR2
            else:
                color = const.DEED_COLOR1

            self.deeds_panel.add_deed(deed, color)

    def saving_cycle(self):
        """Цикл сохранения. Раз в SAVE_CYCLE_TIME сек. сохраняет данные из StopWatchSelector."""
        if not self.saving:
            return

        self.save()
        self.after(const.SAVE_CYCLE_TIME * 1000, self.saving_cycle)

    def _start_saving(self):
        self.saving = True
        self.saving_cycle()

    def _stop_saving(self):
        self.saving = False

    def _restart(self, id_):
        """Изменяет calendar id и перезапускает приложение"""
        self.saver.change_calendar_id(id_)
        self._restart_func()

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


class GraphWindow(Frame, SwitchableWidget):
    """Окно с графиком"""
    _timing_data: list[dict]
    _build_in_window: bool

    def __init__(self, parent, timing_data_handler):
        super().__init__(master=parent, bg=const.FRM_COL1)
        self._timing_data = [{}]
        self.graph_built = False
        self._timing_data_handler = timing_data_handler
        self._build_in_window = False
        self._plan_data = None
        self._place_widgets()

    def _place_widgets(self):
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(0, weight=20)

        self._wdg_period_selector = PeriodCalendar(self)
        self._wdg_period_selector.grid(row=0, column=1, sticky=N + W + E + S)

        graph_build_btn = CTkButton(self, text='Построить график', fg_color=const.BTN_COL, hover_color=const.BTN_HOV_COL,
                                    text_color=const.TEXT_COL, command=self._build_graph)
        graph_build_btn.grid(row=1, column=1, sticky=N + W + E)

        self._wdg_info = FormWidget(self, writeable=False, bg=const.FRM_COL2)
        self._wdg_info.grid(row=2, column=1, sticky=W + E + N)

        self._graph_frm = Frame(self, bg=const.FRM_COL1)
        self._graph_frm.grid(row=0, column=0, rowspan=3, sticky=W + E + N + S)

    def _get_data(self):
        """Получает данные о соответствии плану за период (из метода get_dates виджета wdg_period_selector)"""
        dates = self._wdg_period_selector.get_dates()
        if dates:
            timing_handler = self._timing_data_handler(dates)
            if len(timing_handler.plan_data) > 1:
                self._plan_data = timing_handler.plan_data
            else:
                tkinter.messagebox.showerror(const.PLOT_ERR_TITLE, const.NO_DATES_ERR_MSG)

    def _insert_stat(self):
        if self._plan_data is None:
            return
        for param in self._plan_data[const.INFO]:
            self._wdg_info.add_row(f'{const.NAMES_DICT[param]}:', self._plan_data[const.INFO][param])

    def _build_graph(self):
        """
        Строит график соответствия плану.
        :param plan_data: словарь вида {<дата вида dd.mm.yy>: <процент соответствия плану>}.
        """
        self._get_data()
        if self._plan_data is None:
            return
        if self.graph_built:
            self._delete_graph()
        self._plot_graph()
        self._insert_stat()

    def _plot_graph(self):
        self.graph_built = True
        dates = list(self._plan_data.keys())[1:]
        percents = [(int(self._plan_data[key])) for key in self._plan_data if key != const.INFO]

        figure = Figure(figsize=(5, 5))
        plot = figure.add_subplot(111)
        plot.grid()
        plot.axline(xy1=(0, const.PERMISSIBLE_PERCENT), slope=0, color='r')
        plot.set_ylim(bottom=0, top=100)
        plot.set_yticks([i for i in range(0, 101, 10)])
        plot.plot(dates, percents, marker='o', linestyle='dashed')

        graph_view = FigureCanvasTkAgg(figure, self._graph_frm)
        graph_view.draw()
        graph_view.get_tk_widget().pack(fill=BOTH, expand=True)

    def _delete_graph(self):
        """Удаляет виджет графика (и все другие дочерние виджеты graph_frm). Очищает статистику wdg_info"""
        self.graph_built = False
        self._wdg_info.clear()
        for widget in self._graph_frm.winfo_children():
            widget.destroy()

    def collapse_window(self):
        self.grid_forget()

    def place_window(self):
        self.grid(row=0, column=1, sticky=W + E + N + S)


class Settings(Frame, SwitchableWidget):
    def __init__(self, parent: tkinter.Widget, saver, bg: str):
        super().__init__(master=parent, bg=bg)
        self.settings = {}
        self._saver = saver
        self._themes = {"dark_theme": {"frm_col1": '#262626'}}
        self._place_widgets()

    def _place_widgets(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=12)

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=25)

        frm_color = LabelFrame(self, bg=const.FRM_COL2, text='Внешний вид')
        frm_color.grid(row=0, column=0)

        frm_ignore_deeds = LabelFrame(self, bg=const.FRM_COL2, text='Игнорируемые дела')
        frm_ignore_deeds.grid(row=0, column=0, sticky=N + W + E + S)

        wdg_ignore_deeds = ComboBoxAdd(frm_ignore_deeds, bg=const.BTN_COL, save_func=Saver.add_ignore_deed, del_func=Saver.del_ignore_deed, values=Saver.get_ignoring_deeds())
        wdg_ignore_deeds.grid(row=0, column=0, sticky=W + E)

        frm_other_settings = LabelFrame(self, bg=const.FRM_COL2, highlightthickness=0, text='Другое')
        frm_other_settings.grid(row=0, column=1, sticky=N + W + E + S)

        calendar_id = Saver.get_calendar_id()
        wdg_calendar_id = AllowingEntry(frm_other_settings, bg=const.BTN_COL, fg=const.TEXT_COL, default_value=calendar_id, confirm_callback=Saver.change_calendar_id)
        wdg_calendar_id.grid(row=0, column=0)

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
    master = Frame(root, bg=const.FRM_COL1)
    master.pack(fill=BOTH, expand=True)

    master.columnconfigure(1, weight=15)
    master.rowconfigure(0, weight=1)

    window = Window(master, const.FRM_COL2, Saver, lambda: restart(root))
    window.grid(row=0, column=1, sticky=W + E + N + S)

    graph = GraphWindow(master, TimingDataHandler)
    settings = Settings(master, Saver, const.FRM_COL1)

    menu = Menu(master, window, {'ЧАСЫ': window, 'СТАТ': graph, 'НАСТР': settings}, const.FRM_COL2, const.BTN_COL)
    menu.grid(row=0, column=0, sticky=W + E + N + S)

    root.iconbitmap('icons\\logo.ico')
    root.mainloop()


def restart(root: Tk):
    root.destroy()
    launch()


if __name__ == '__main__':
    launch()
