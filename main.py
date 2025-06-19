from tkinter import Frame, Tk, BOTH, W, E, Y, N, S
from customtkinter import CTkButton, CTkComboBox

from widgets import DeedsList, StopWatch, COLOR3, DeedsPanel, Menu
from data_processing import APIProcessor

class Window:
    def __init__(self):
        PATH = 'data'
        self.day_data = ''
        self.buttons = ((master), (master))
        try:
            self.get_data()
        except ... : #ToDo: добавить конкретную ошибку после начала работы с API
            print('Ошибка при получении данных из Google Calendar, попробуйте ещё раз')
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


        wdg_deeds_selector = CTkComboBox(wdg_frame) #ToDo: продумать случай изменения плана

        wdg_stop_watch = StopWatch(wdg_frame) # секундомер
        wdg_stop_watch.grid(row=1, column=0, columnspan=2, sticky=W+E)

        # панель с планом
        self.deeds_panel.grid(row=0, column=3, sticky=W + E + N + S)

    def get_data(self):

        data_processor = APIProcessor()
        self.day_data = data_processor.get_data()

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

    Window()

    root.mainloop()
