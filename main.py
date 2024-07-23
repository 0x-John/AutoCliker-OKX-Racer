import os
import time
import random
import cv2
import keyboard
import mss
import numpy as np
import pygetwindow as gw
import win32api
import win32con
import warnings
from pywinauto import Application
import config

warnings.filterwarnings("ignore", category=UserWarning, module='pywinauto')

def list_windows_by_title(title_keywords):
    windows = gw.getAllWindows()
    filtered_windows = []
    for window in windows:
        for keyword in title_keywords:
            if keyword.lower() in window.title.lower():
                filtered_windows.append((window.title, window._hWnd))
                break
    return filtered_windows

class Logger:
    def __init__(self, prefix=None):
        self.prefix = prefix

    def log(self, data: str):
        if self.prefix:
            print(f"{self.prefix} {data}")
        else:
            print(data)

class AutoClicker:
    def __init__(self, hwnd, logger, num_cycles):
        self.hwnd = hwnd
        self.logger = logger
        self.num_cycles = num_cycles
        self.running = False
        self.iteration_count = 0
        self.last_check_time = time.time()

    @staticmethod
    def click_at(x, y):
        try:
            if not (0 <= x < win32api.GetSystemMetrics(0) and 0 <= y < win32api.GetSystemMetrics(1)):
                raise ValueError(f"Координаты вне пределов экрана: ({x}, {y})")
            win32api.SetCursorPos((x, y))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
        except Exception as e:
            print(f"Ошибка при установке позиции курсора: {e}")

    def toggle_script(self):
        self.running = not self.running
        if self.running:
            self.logger.log('Скрипт запущен.')
        else:
            self.logger.log('Скрипт остановлен.')

    def find_and_click(self, templates, sct, monitor):
        matched_locations = {}

        for template_path in templates:
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                self.logger.log(f"Не удалось загрузить файл шаблона: {template_path}")
                continue

            template_height, template_width = template.shape
            img = np.array(sct.grab(monitor))
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)

            res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)

            if max_val >= config.THRESHOLD:
                cX = max_loc[0] + template_width // 2 + monitor["left"]
                cY = max_loc[1] + template_height // 2 + monitor["top"]
                matched_locations[template_path] = (cX, cY)

        if matched_locations:
            selected_template = random.choice(list(matched_locations.keys()))
            location = matched_locations[selected_template]
            self.click_at(location[0], location[1])
            self.logger.log(f'Нажал на шаблон: {selected_template}')
            return True
        return False

    def click_template_areas(self):
        app = Application().connect(handle=self.hwnd)
        window = app.window(handle=self.hwnd)
        window.set_focus()

        templates = ["moon.png", "doom.png"]
        cycle_count = 0

        with mss.mss() as sct:
            keyboard.add_hotkey(config.HOTKEY, self.toggle_script)
            self.logger.log(f'Нажмите {config.HOTKEY} для запуска/остановки скрипта.')

            while True:
                if self.running:
                    if cycle_count >= self.num_cycles:
                        wait_time = self.num_cycles * 90 + 5
                        self.logger.log(f'Выполнено {self.num_cycles} циклов, пауза {wait_time} секунд.')
                        time.sleep(wait_time)
                        cycle_count = 0

                    rect = window.rectangle()
                    monitor = {
                        "top": rect.top,
                        "left": rect.left,
                        "width": rect.width(),
                        "height": rect.height()
                    }

                    if self.find_and_click(templates, sct, monitor):
                        cycle_count += 1
                        wait_time = random.uniform(9, 15)  # Random wait time between 9 and 15 seconds
                        self.logger.log(f'Ждем {wait_time:.2f} секунд.')
                        time.sleep(wait_time)
                    else:
                        self.logger.log('Шаблоны не найдены.')
                time.sleep(0.1)

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)

    windows = list_windows_by_title(config.KEYWORDS)

    if not windows:
        print("Нет окон, содержащих указанные ключевые слова.")
        exit()

    print("Доступные окна для выбора:")
    for i, (title, hwnd) in enumerate(windows):
        print(f"{i + 1}: {title}")

    choice = int(input("Введите номер окна: ")) - 1
    if choice < 0 or choice >= len(windows):
        print("Неверный выбор.")
        exit()

    hwnd = windows[choice][1]

    while True:
        try:
            num_cycles = int(input("Введите количество делений в баке: "))
            if num_cycles > 0:
                break
            else:
                print("Пожалуйста, введите положительное целое число.")
        except ValueError:
            print("Неверный формат. Пожалуйста, введите целое число.")

    logger = Logger("[https://t.me/x_0xJohn]")
    logger.log("Вас приветствует бесплатный скрипт - автокликер.")

    auto_clicker = AutoClicker(hwnd, logger, num_cycles)
    try:
        auto_clicker.click_template_areas()
    except Exception as e:
        logger.log(f"Произошла ошибка: {e}")
    for i in reversed(range(5)):
        print(f"Скрипт завершит работу через {i}")
        time.sleep(1)
