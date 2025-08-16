import datetime
import tkinter
import typing as tp
from queue import Queue
from tkinter import Frame, Label, Button, NORMAL, END, W, E, S, N, TOP, DISABLED, StringVar, Entry, Text
import tkinter.ttk as ttk

from customtkinter import CTkEntry, CTkButton, CTkSwitch, CTkFrame, CTkProgressBar
from tk_tools import Calendar

import time
from threading import Thread
import re

from base import (FRM_COL1, BTN_COL, COMMON_FONT, DAY_ROWS, MINS_IN_ROW, CBOX_DEFAULT, START_TEXT, STOP_TEXT, COMMON_FONT_COLOR, CURRENT_DEED,
                  IGNORING_COLOR, IGNORING_TEXT_COLOR, IGNORING_TEXT, TIME_MAIN, TIME_DEED, NAME, TIME_START, TIME_END,
                  TIME, READONLY, DEFAULT_TIME, time_to_sec, rm_insignificant_zeros, LAST_BREAK_TEXT, TIME_VIEW_FORMAT,
                  DATE_FORMAT, HEADER_FONT, FRM_COL2)
from support_classes import SwitchableWidget


class ComboBox(ttk.Combobox):
    """Обёртка для ttk.Combobox. Обрабатывает список входных значений (values)"""
    def __init__(self, parent, state: str = NORMAL):
        super().__init__(master=parent, state=READONLY, font=HEADER_FONT)
        self.set(CBOX_DEFAULT)

    def process_values(self, values: tuple | list) -> list:
        """Удаляет из кортежа входящих значений дубликаты элементов. Пример: ("name", "name") -> ["name"] """
        output_values = []
        for value in values:
            if value in output_values:
                continue
            output_values.append(value)

        return output_values

    def clear(self):
        """Вызывается из StopWatchSelector при изменении плана. Очищает список дел"""
        self.configure(values=[])

    def load_deeds(self, deeds: tuple):
        """Загружает названия дел в Combobox"""
        self.configure(values=self.process_values(deeds))


class StopWatchSelector(Frame):

    #Константы события

    START = 'start'   # Отсчёт запущен
    STOP = 'stop'  # Отсчёт остановлен
    DEED_CHANGED = 'deed_changed'  # Дело изменено
    LAUNCH = 'launch'  # Запуск программы

    # Индексы значений времени секундомеров в очереди
    MAIN_TIME_IDX = 0
    DEED_TIME_IDX = 1

    def __init__(self, parent, deed_request):
        super().__init__(master=parent)
        self.deed_request = deed_request
        self.data = {
            CURRENT_DEED: '',
            TIME_MAIN: '',
            TIME_DEED: ''
        }

        self.place_widgets()
        self.counting = False  # Идёт ли отсчёт

    def place_widgets(self):

        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)

        self.wdg_selector = ComboBox(self)
        self.wdg_selector.grid(row=0, column=0, columnspan=2, sticky=W + E)
        self.wdg_selector.bind('<<ComboboxSelected>>', self.change_deed)

        self.wdg_main_swatch = CTkEntry(self, font=COMMON_FONT)
        self.wdg_main_swatch.grid(row=1, column=0, sticky=W + E)
        self.sw_insert(self.wdg_main_swatch, DEFAULT_TIME)

        self.wdg_deed_swatch = CTkEntry(self, font=COMMON_FONT)
        self.wdg_deed_swatch.grid(row=1, column=1, sticky=W + E)
        self.sw_insert(self.wdg_deed_swatch, DEFAULT_TIME)

        self.start_btn = CTkButton(self, text=START_TEXT, command=self.start)
        self.start_btn.grid(row=2, column=0, sticky=W)

        self.stop_btn = CTkButton(self, text=STOP_TEXT, state=DISABLED, command=self.stop)
        self.stop_btn.grid(row=2, column=1, sticky=W)

        self.lbl_last_break = Label(self, text=LAST_BREAK_TEXT)
        self.lbl_last_break.grid(row=3, column=0, columnspan=2, sticky=W)

    def start(self):

        if self.wdg_selector.get() == CBOX_DEFAULT:  # На случай включённой кнопки при CBOX_DEFAULT в селекторе
            return

        self.counting = True  # флаг для цикла отсчёта
        self.count_time(self.wdg_main_swatch)
        self.count_time(self.wdg_deed_swatch)

        self.change_wdg_state(self.START)

    def stop(self):
        self.change_wdg_state(self.STOP)
        self.lbl_last_break.configure(text=f'{LAST_BREAK_TEXT}{datetime.datetime.now().strftime(TIME_VIEW_FORMAT)}')

        self.counting = False

    def sw_insert(self, widget, text: str):
        widget.configure(state=NORMAL)

        widget.delete(0, END)
        widget.insert(0, text)

        widget.configure(state=READONLY)

    def load_deed(self, deed_data: dict):
        """Вводит нужные значения в Combobox и секундомеры при запуске с созданным temp_json"""

        self.wdg_selector.set(deed_data[CURRENT_DEED])
        self.sw_insert(self.wdg_main_swatch, deed_data[TIME_MAIN])
        self.sw_insert(self.wdg_deed_swatch, deed_data[TIME_DEED])
        self.change_wdg_state(self.LAUNCH)  # Изменение состояния

    def load_deeds(self, deeds: tuple):
        """Загружает список дел в Combobox"""
        self.wdg_selector.load_deeds(deeds)

    def to_default(self):
        """Вызывается из Window при изменении плана. Устанавливает начальные значения в """
        if self.counting:
            self.stop()

        self.wdg_selector.set(CBOX_DEFAULT)
        self.wdg_selector.clear()
        self.sw_insert(self.wdg_main_swatch, DEFAULT_TIME)
        self.sw_insert(self.wdg_deed_swatch, DEFAULT_TIME)
        # В данном случае из Window последовательно вызываются to_default и load_deed, т.е. состояние будет изменено на состояние при запуске

    def change_wdg_state(self, event: str):
        """Меняет состояние wdg_selector, start_btn и stop_btn в зависимости от события. Меняет main_time и deed_time"""

        if event == self.START:
            self.wdg_selector.configure(state=DISABLED)
            self.start_btn.configure(state=DISABLED)
            self.stop_btn.configure(state=NORMAL)

        elif event == self.STOP:
            self.wdg_selector.configure(state=READONLY)
            self.start_btn.configure(state=NORMAL)
            self.stop_btn.configure(state=DISABLED)

        elif event == self.LAUNCH:
            if self.wdg_selector.get() == CBOX_DEFAULT:
                self.start_btn.configure(state=DISABLED)

        elif event == self.DEED_CHANGED:
            self.start_btn.configure(state=NORMAL)

    def change_deed(self, _):
        """Вызывается при смене дела в CTkCombobox. Изменяет состояние кнопки start_btn, меняет current_deed, вводит в секундомер дела
           значение из основного JSON'a"""
        deed = self.wdg_selector.get()
        plan_data = self.deed_request(deed)
        self.sw_insert(self.wdg_deed_swatch, plan_data)

        self.change_wdg_state(self.DEED_CHANGED)

    def get_current_data(self) -> dict:
        """Предназначено для вызова из Window. Возвращает словарь с актуальными данными для записи во временный JSON"""
        self.data[CURRENT_DEED] = self.wdg_selector.get()
        self.data[TIME_MAIN] = self.wdg_main_swatch.get()
        self.data[TIME_DEED] = self.wdg_deed_swatch.get()

        return self.data

    def count_time(self, widget):
        if not self.counting:
            return

        self.after(1000, lambda: self.count_time(widget))

        secs = time_to_sec(widget.get())

        secs += 1
        minutes = str((secs // 60) % 60).rjust(2, '0')
        hours = str(secs // 3600).rjust(2, '0')

        self.sw_insert(widget, f'{hours}:{minutes}:{str(secs % 60).rjust(2, '0')}')


class DeedsPanel(Frame):
    """Панель с делами. Параметр change_saver - static-метод класса Saver, передаваемый в экземпляры класса Deed"""
    deeds: list

    def __init__(self, parent, change_saver, state_checker):
        super().__init__(master=parent, highlightthickness=3, highlightbackground=FRM_COL2)
        self.change_saver = change_saver
        self.state_checker = state_checker

        self.deeds = []
        self.place_widgets()
        self.mark_panel()

    def place_widgets(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=4)

        row = 0
        for hour in range(24):
            wdg_hour = Label(self, text=f'{hour}', font=('Verdana', 10))
            wdg_hour.grid(row=row, column=0, rowspan=4, sticky=N + E)
            row += 4

    def mark_panel(self):
        """Создаёт разметку панели. 1-я, а затем каждая 4-я линии обозначают границы часа."""
        for i in range(DAY_ROWS):
            self.rowconfigure(i, weight=1)
            if i % 4 == 0:
                bg = "Black"
            else:
                bg = BTN_COL
            mark = Frame(self, bg=bg)
            mark.grid(row=i, column=1, sticky=W + E)

    def add_deed(self, deeds: dict, deed_color: str):
        """Добавляет мероприятие на панель. deeds в виде {"name": название дела, "time_start": время начала, "time_end": время окончания}
           Время в формате: hh:mm. Предполагается, что время в минутах кратно 15-ти, т.е.:00:00, 00:15, 00:30, 00:45 и т.д."""

        time_start = deeds[TIME_START].split(':') # "19:00" -> ["19", "00"]
        time_end = deeds[TIME_END].split(':')

        hours_start = rm_insignificant_zeros(time_start[0])
        mins_start = rm_insignificant_zeros(time_start[1])

        hours_end = rm_insignificant_zeros(time_end[0])
        mins_end = rm_insignificant_zeros(time_end[1])

        # Вычисление строки в таблице
        row_start = round((hours_start * 60 + mins_start) / MINS_IN_ROW)  # Находим общее количество минут с 00:00 и
        row_end = round((hours_end * 60 + mins_end) / MINS_IN_ROW)        # делим на 15 (число минут в одной строке)

        if row_start > row_end:  # обработка случая окончания дела на следующий день, пример: 21:00 - 00:15
            row_end = DAY_ROWS

        # Настройка виджета

        deed_wdg = Deed(self, deed_name=deeds[NAME], time_start=deeds[TIME_START], time_end=deeds[TIME_END], color=deed_color,
                        text_color=COMMON_FONT_COLOR, change_saver=self.change_saver, state_checker=self.state_checker)
        deed_wdg.grid(row=row_start, column=1, rowspan=row_end - row_start, sticky=W + E + N + S)
        self.deeds.append(deed_wdg)  # добавление экземпляра класса deed в список виджетов дел

    def clear_panel(self):
        """Очищает панель. Удаляет все виджеты дел"""
        for deed in self.deeds:
            deed.destroy()


class Deed(Frame):
    """Виджет дела (мероприятия), размещаемый на панели DeedsPanel. Параметр change_saver принимает static-метод класса
       Saver для добавления времени дела в игнорируемое время (main_json[plan_time][ignoring_time]); state_checker -
       static-метод класса Saver для получения состояния виджета (игнорируется/не игнорируется)"""

    def __init__(self, master, deed_name: str, time_start: str, time_end: str, color: str, text_color: str,
                 change_saver, state_checker):
        super().__init__(master=master, bg=color)

        self.deed_name = deed_name
        self.time_start = time_start
        self.time_end = time_end
        self.color = color
        self.change_saver = change_saver
        self.text_color = text_color

        self.place_widgets()
        state = state_checker(time_start, time_end, deed_name)

        if state:  # Проверка на игнорирование дела
            self.changing_btn.select()

        self.change_wdg_state(state)

    def place_widgets(self):
        self.name_lbl = Label(self, text=self.deed_name, bg=self.color, fg=self.text_color, font=HEADER_FONT)
        self.name_lbl.grid(row=0, column=0, columnspan=2)

        self.time_lbl = Label(self, text=f'{self.time_start}-{self.time_end}', bg=self.color, fg=self.text_color, font=COMMON_FONT)
        self.time_lbl.grid(row=1, column=0)

        self.changing_btn = CTkSwitch(self, bg_color=self.color, text=IGNORING_TEXT, command=self.change_ign_state, font=COMMON_FONT,
                                      text_color=self.text_color)
        self.changing_btn.grid(row=1, column=2)

    def change_ign_state(self):
        """Обёртка над change_saver. Передаёт в change_saver состояние кнопки changing_btn и вызывает change_wdg_state
           для смены состояния виджета."""
        self.change_wdg_state(self.changing_btn.get())
        self.change_saver(self.deed_name, self.time_start, self.time_end, bool(self.changing_btn.get()))

    def change_wdg_state(self, state: int):
        """Меняет состояние виджета. Возможные состояния: 0 - обычное, 1 - дело игнорируется.
           Зависит от состояния переключателя changing_btn"""

        if state:
            self.configure(bg=IGNORING_COLOR)
            self.name_lbl.configure(bg=IGNORING_COLOR, fg=IGNORING_TEXT_COLOR)
            self.time_lbl.configure(bg=IGNORING_COLOR, fg=IGNORING_TEXT_COLOR)
            self.changing_btn.configure(text_color=IGNORING_TEXT_COLOR)
        else:
            self.configure(bg=self.color)
            self.name_lbl.configure(bg=self.color, fg=self.text_color)
            self.time_lbl.configure(bg=self.color, fg=self.text_color)
            self.changing_btn.configure(text_color=self.text_color)


class Menu(Frame):
    """
    Класс меню. parent - родительский виджет, window_now - окно, размещённой в момент создания экземпляра, switch_data -
    словарь вида {<название окна>: <экземпляр класса окна>}. Каждый экзмепляр класса окна должен иметь методы collapse_window
    и place_window (1-й отвечает за уничтожение виджета, 2-й - за размещение).
    """

    def __init__(self, parent: tkinter.Widget, window_now: SwitchableWidget, switch_data: dict, bg: str, btn_bg: str):
        super().__init__(master=parent, bg=bg)
        self.switch_data = switch_data
        self.window_now = window_now
        self._btn_bg = btn_bg
        self._place_widgets()

    def _place_widgets(self):
        for row, window_name in enumerate(self.switch_data.keys()):
            switching_window = self.switch_data[window_name]
            btn = Button(self, relief="flat", overrelief="ridge", bg=self._btn_bg, activebackground=self._btn_bg, cursor='hand2', text=window_name,
                         command=lambda window=switching_window: self._change_window(window))
            btn.grid(row=row, column=0, sticky=W + E)

    def _change_window(self, switching_window):
        """
        Переключает текущее окно на заданное в параметре switching_window. Для каждой кнопки на панели Menu он свой.
        """
        if self.window_now == switching_window:  # проверка на то, является ли переключаемое окно текущим
            return

        self.window_now.collapse_window()
        switching_window.place_window()
        self.window_now = switching_window  # Обновление window_now

    def change_window(self, window_num: int):
        """Переключает окно по его номеру. Предназначен для вызова за пределами класса."""
        if window_num >= len(self.switch_data):
            return
        self._change_window(list(self.switch_data.keys())[window_num])


class DialogWindow(Frame):
    def __init__(self, master, text: str, btn_text: str, args: list = None, command=None):
        super().__init__(master=master)
        self.args = args
        self.command = command

        lbl = Label(self, text=text)
        lbl.grid(row=0, column=0, columnspan=3)

        btn = CTkButton(self, text=btn_text, command=self.action)
        btn.grid(row=0, column=1)

    def action(self):
        """Вызывается при нажатии на кнопку"""
        if self.command is not None:
            if self.args is None:
                self.command()
            else:
                self.command(self.args)

        self.destroy()


class PeriodEntry(CTkEntry):
    """
    Модифицированный tkinter.Entry с валидацией, пропускающей только цифры 0-9, точку (.) и дефис (-).
    Имеет текст по умолчанию.
    """
    DEFAULT_TEXT = 'dd.mm.yy-dd.mm.yy'
    ALLOWED_CHARS = ('.', '-')
    EXPR_FOR_RANGE = '^(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.([0-9]{2})-(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.([0-9]{2})$'
    #  регулярное выражение для проверки даты в формате dd.mm.yy-dd.mm.yy

    def __init__(self, master):
        super().__init__(master=master)
        self.configure(validate="key", validatecommand=(self.register(self.__check_state), '%S'))

    def __check_state(self, char) -> bool:
        """Валидирует виджет и вводит в него текст по умолчанию, если в нём нет символов."""
        if char.isdigit() or char in self.ALLOWED_CHARS:
            return True
        else:
            return False

    def get_dates(self) -> list[str] | bool:
        """Возвращает список дат из диапазона, введённого в виджет в виде dd.mm.yy-dd.mm.yy. Если ввод некорректен,
           возвращает False"""
        range_ = self.get()
        if re.match(self.EXPR_FOR_RANGE, range_):
            start_date, end_date = range_.split('-')
            start_date = datetime.datetime.strptime(start_date, DATE_FORMAT)
            end_date = datetime.datetime.strptime(end_date, DATE_FORMAT)

            start_date = min(start_date, end_date)
            end_date = max(start_date, end_date)

            dates = []
            delta = end_date - start_date
            for day in range(delta.days + 1):
                date_ = start_date + datetime.timedelta(day)
                dates.append(str(date_.strftime("%d.%m.%y")))
            return dates
        else:
            return False


class ColorFrame(Frame):

    _color_name: str
    _color: str | None

    def __init__(self, color_name: str, *args, **kwargs):
        from base import config

        super().__init__(*args, **kwargs)
        self._color_name = color_name

        if self._color_name in config:
            self._color = config[self._color_name]
        else:
            raise ValueError(f'Unknown color name: {self._color_name}')

        self._place_widgets()

    def _place_widgets(self):
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=2)
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=1)

        color_name = Label(self, text='color_name')
        color_name.grid(row=0, column=0, columnspan=2)

        wdg_color_view = Frame(self, bg=self._color)
        wdg_color_view.grid(row=1, column=0, sticky=W + E + N + S)


class SmartButton(Button):
    _tooltip: None | tkinter.Widget

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tooltip = None

    def set_tooltip(self, text: str = f'{Button.__name__}', time_: int = 1000):
        if self._tooltip:
            self._tooltip = Label(self, text=text)
            self.bind('<Enter>', lambda event: self._init_tooltip(event, time_))

    def _init_tooltip(self, event, time_: int):
        call = self.after(time_, lambda: self._show_tooltip(event.x, event.y))
        self.bind('<Leave>', lambda _: self.after_cancel(call))

    def _show_tooltip(self, x: int, y: int):
        self._tooltip.place(x=x, y=y)
        self.bind('<Leave>', self._hide_tooltip)

    def _hide_tooltip(self, event):
        self._tooltip.destroy()
        self.bind('<Enter>', )

    def _del_tooltip(self):
        self._tooltip = None


class ComboBoxAdd(Frame):
    """
    Combobox с возможностью удаления и добавления элементов.

    :param save_func: функция сохранения, должна принимать один аргумент - добавляемое значение
    :param del_func: функция удаления, должна принимать один аргумент - удаляемое значение
    :param values: кортеж/список значений виджета
    """

    def __init__(self, *args, bg: str = 'White', save_func: tp.Callable = None, del_func: tp.Callable = None, values: tuple | list, **kwargs):
        super().__init__(*args, **kwargs)

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self._save_func = save_func
        self._del_func = del_func

        self._combobox = ttk.Combobox(self, values=values)
        self._combobox.grid(row=0, column=0, columnspan=2, sticky=W + E)

        self._window_del = DialogWindow(self, text='', btn_text='Удалить', args=[], command=self._del_value)

        btn_add = Button(self, text='Добавить', relief='flat', bg=bg, command=self._add_value)
        btn_add.grid(row=1, column=0, sticky=W + E)

        btn_del = Button(self, text='Удалить', relief='flat', bg=bg, command=self._del_value)
        btn_del.grid(row=1, column=1, sticky=W + E)

    def _add_value(self):
        values = list(self._combobox.cget('values'))
        new_value = self._combobox.get()

        if new_value not in values and new_value != '':
            values.append(new_value)
            self._combobox.configure(values=values)
            if self._save_func is not None:
                self._save_func(new_value)
            self._combobox.delete(0, END)

    def _del_value(self):
        value = self._combobox.get()
        values = list(self._combobox.cget('values'))

        if value in values:
            values.remove(value)
            self._combobox.configure(values=values)
            if self._del_func is not None:
                self._del_func(value)
            self._combobox.delete(0, END)


class AllowingEntry(Frame):
    """
    Entry с кнопками подтверждения ввода нового значения и ввода значения по умолчанию.
    :param default_value: значение по умолчанию
    :param confirm_callback: вызываемый объект, принимающий 1 аргумент - текст виджета.

    """

    def __init__(self, *args, bg: str = 'White', fg: str = 'Black', default_value: str = '', confirm_callback: tp.Callable = lambda _: None):
        super().__init__(*args, bg=bg)
        self._default_value = default_value
        self._confirm_callback = confirm_callback

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=4)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        self._entry = Entry(self, bg=bg, fg=fg)
        self._entry.grid(row=0, column=0)
        self._entry.insert(0, self._default_value)

        btn_confirm = Button(self, text='conf', relief='flat', cursor='hand2', command=self._confirm)
        btn_confirm.grid(row=0, column=1)

        btn_to_default = Button(self, text='reset', relief='flat', cursor='hand2', command=self._reset)
        btn_to_default.grid(row=0, column=2)

    def _confirm(self):
        self.focus_set()
        self._confirm_callback(self._entry.get())

    def _reset(self):
        self._entry.delete(0, END)
        self._entry.insert(0, self._default_value)


class DialogInput(Frame):

    _title: str
    _message: str
    _label: str
    _confirm_command: tp.Callable
    _default_text: str
    _confirm_btn_text: str

    def __init__(self,
                 master: None | tkinter.Widget = None,
                 title: str = '',
                 message: str = '',
                 label: str = '',
                 default_text: str = '',
                 confirm_btn_text: str = 'OK',
                 confirm_command: tp.Callable = lambda _: None):
        super().__init__(master)
        self._title = title
        self._message = message
        self._label = label
        self._default_text = default_text
        self._confirm_btn_text = confirm_btn_text
        self._confirm_command = confirm_command

        self._place_widgets()

    def _place_widgets(self):
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=3)
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=4)
        self.columnconfigure(1, weight=4)
        self.columnconfigure(2, weight=1)

        wdg_title = Label(self, text=self._title, font=('Arial', 14), relief='flat', cursor='ibeam')
        wdg_title.grid(row=0, column=0, columnspan=3, sticky=W + E + N + S)

        wdg_message = Text(self, font=('Arial', 12), relief='flat')
        wdg_message.grid(row=1, column=0, columnspan=3, sticky=W + E)
        wdg_message.insert(1.0, self._message)
        wdg_message.configure(state='disabled')

        wdg_label = Label(self, text=self._label, font=('Arial', 12), relief="flat")
        wdg_label.grid(row=2, column=0)

        self._wdg_entry = Entry(self)
        self._wdg_entry.insert(0, self._default_text)
        self._wdg_entry.grid(row=2, column=1)

        btn_confirm = Button(self, relief="flat", cursor="hand2", text=self._confirm_btn_text, command=self._confirm)
        btn_confirm.grid(row=2, column=2)

    def _confirm(self):
        text = self._wdg_entry.get()
        self.destroy()
        self._confirm_command(text)


class PeriodCalendar(Frame):
    """Надстройка над tk_tools.groups.Calendar, позволяющая выбрать диапазон дат"""

    def __init__(self, master: tkinter.Widget):
        super().__init__(master)
        self._calendar = Calendar(self, callback=self._set_first_point)
        self._first_point = None
        self._second_point = None

    def _place_widgets(self):
        self.rowconfigure(0, weight=2)
        self.rowconfigure(1, weight=1)

        self._period_view = Label(self)
        self._period_view.grid(row=1, column=0)

    def _set_first_point(self):
        if self._second_point is not None:
            self._second_point = None

        self._calendar.callback = self._set_second_point
        self._first_point = self._calendar.selection
        self._period_view.configure(text=f'{self._first_point}')

    def _set_second_point(self):
        self._calendar.callback = self._set_first_point
        self._second_point = self._calendar.selection
        self._period_view.configure(text=f'{self._first_point} - {self._second_point}')
    def get(self) -> tuple[str, ...]:
        if self._first_point is not None and self._second_point is not None:
            return self._first_point, self._second_point

    def get_dates(self) -> list[str] | None:
        """Возвращает список дат из выбранного пользователем диапазона. Если диапазон не выбран, возвращает None"""
        range_ = self.get()

        if range_ is None:
            return

        start_date, end_date = range_
        start_date = datetime.datetime.strptime(start_date, DATE_FORMAT)
        end_date = datetime.datetime.strptime(end_date, DATE_FORMAT)

        start_date = min(start_date, end_date)
        end_date = max(start_date, end_date)

        dates = []
        delta = end_date - start_date
        for day in range(delta.days + 1):
            date_ = start_date + datetime.timedelta(day)
            dates.append(str(date_.strftime("%d.%m.%y")))
        return dates
