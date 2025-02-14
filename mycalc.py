import sys, os, json, configparser
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QListWidget, QFileDialog, QMessageBox, QLabel, QMenuBar, QMenu)
from PyQt6.QtGui import QIcon, QPixmap, QDesktopServices
from PyQt6.QtCore import Qt, QUrl
from addexpedition import AddExpeditionWidget
from mainworks import MainWorksWidget

class IOExpedition:
    def __init__(self):
        """
        Конструктор класса IOExpedition.
        Инициализирует настройки (settings) из файла init.ini.
        Если файла нет, создаёт файл по умолчанию.
        Также загружает список недавних файлов.
        """
        self.settings = configparser.ConfigParser()
        if os.path.exists('init.ini'):
            self.settings.read('init.ini', encoding='utf-8')
        else:
            self.create_default_ini()
        self.recent_files = self.get_recent_files()

    def create_default_ini(self):
        """
        Создаёт файл init.ini по умолчанию с пустым списком недавних файлов.
        """
        self.settings['Recent Files'] = {'files': '[]'}
        self.save_ini_file()

    def save_ini_file(self):
        """
        Сохраняет текущие настройки в файл init.ini.
        """
        with open('init.ini', 'w', encoding='utf-8') as configfile:
            self.settings.write(configfile)

    def get_recent_files(self):
        """
        Возвращает список недавних файлов, считанный из настроек.
        Если таких файлов нет, возвращает пустой список.
        """
        if 'Recent Files' in self.settings:
            files = json.loads(self.settings['Recent Files'].get('files', '[]'))
            return files
        return []

    def populate_recent_files_menu(self):
        """
        Заполняет меню недавних файлов.
        Если список пустой, отключает меню; иначе добавляет пункты меню с файлами.
        Каждый пункт меню привязан к методу open_recent_file.
        """
        self.recent_files_menu.clear()
        if not self.recent_files:
            self.recent_files_menu.setEnabled(False)
        else:
            self.recent_files_menu.setEnabled(True)
            for file in self.recent_files:
                action = self.recent_files_menu.addAction(file)
                # Лямбда-функция для захвата имени файла по умолчанию
                action.triggered.connect(lambda checked=False, filename=file: self.open_recent_file(filename))

    def open_recent_file(self, filename):
        """
        Открывает выбранный недавно использованный файл.
        Если файл существует, использует метод open_hike для загрузки.
        Если файла нет, выводит предупреждение и обновляет список недавних файлов.
        После успешного открытия активирует действия сохранения и закрытия.
        """
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as file:
                    hike = json.load(file)
                    
                self.current_file = filename
                # Активация действий сохранения и закрытия
                if hasattr(self, "save_action"):
                    self.save_action.setEnabled(True)
                if hasattr(self, "save_as_action"):
                    self.save_as_action.setEnabled(True)
                if hasattr(self, "close_action"):
                    self.close_action.setEnabled(True)
                    
                # Открываем поход в главном окне
                self.show_main_works_widget(hike)
                
                # Обновляем список недавних файлов
                if filename in self.recent_files:
                    self.recent_files.remove(filename)
                self.recent_files.insert(0, filename)
                if len(self.recent_files) > 5:
                    self.recent_files.pop()
                self.save_recent_files()
                self.populate_recent_files_menu()
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл: {str(e)}")
        else:
            QMessageBox.warning(self, "Ошибка", f"Файл {filename} не найден.")
            if filename in self.recent_files:
                self.recent_files.remove(filename)
            self.save_recent_files()
            self.populate_recent_files_menu()

    def save_recent_files(self):
        """
        Сохраняет текущий список недавних файлов в настройки и записывает их в init.ini.
        """
        self.settings['Recent Files'] = {'files': json.dumps(self.recent_files)}
        self.save_ini_file()

    def get_unique_filename(self, base_filename):
        """
        Генерирует уникальное имя файла на основании базового имени.
        Если файл с таким именем уже существует, добавляет (n) к имени.
        """
        if not os.path.exists(base_filename):
            return base_filename

        name, ext = os.path.splitext(base_filename)
        counter = 1
        while True:
            new_filename = f"{name}({counter}){ext}"
            if not os.path.exists(new_filename):
                return new_filename
            counter += 1

    def get_hike_data(self):
        """
        Получает данные текущего похода для сохранения.
        Формирует словарь с именем похода, участниками, датами, днями трека и расходами.
        """
        if hasattr(self, 'main_works_widget'):
            # Get expenses data from table
            expenses_data = []
            num_participants = len(self.main_works_widget.hike_data['participants'])
            num_days = self.main_works_widget.hike_data['track_days']
            
            for row in range(num_days):  # Exclude total row
                day_expenses = []
                for col in range(1, num_participants + 1):  # Skip date column
                    item = self.main_works_widget.table.item(row, col)
                    expense = item.text() if item else "0"
                    day_expenses.append(expense)
                expenses_data.append(day_expenses)

            return {
                "hike_name": self.main_works_widget.hike_data['hike_name'],
                "participants": self.main_works_widget.hike_data['participants'],
                "start_date": self.main_works_widget.hike_data['start_date'],
                "end_date": self.main_works_widget.hike_data['end_date'],
                "track_days": self.main_works_widget.hike_data['track_days'],
                "expenses_data": expenses_data
            }
        elif hasattr(self, 'create_hike_widget'):
            num_participants = self.create_hike_widget.participant_fields.count()
            num_days = self.create_hike_widget.track_days.value()
            
            # Create initial expenses array filled with zeros
            expenses_data = [["0"] * num_participants for _ in range(num_days)]
            
            return {
                "hike_name": self.create_hike_widget.hike_name.currentText(),
                "participants": [
                    {
                        "name": self.create_hike_widget.participant_fields.itemAt(i).layout().itemAt(0).widget().text() or f"Участник {i + 1}",
                        "payment": self.create_hike_widget.participant_fields.itemAt(i).layout().itemAt(1).widget().value()
                    }
                    for i in range(num_participants)
                ],
                "start_date": self.create_hike_widget.start_date.date().toString(Qt.DateFormat.ISODate),
                "end_date": self.create_hike_widget.end_date.date().toString(Qt.DateFormat.ISODate),
                "track_days": num_days,
                "expenses_data": expenses_data
            }
        else:
            QMessageBox.warning(self, "Ошибка", "Нет активного похода для сохранения")
            return None

    def open_hike(self, filename=None):
        """
        Открывает файл с данными похода.
        Показывает диалог выбора файла, загружает данные и обновляет интерфейс.
        
        Args:
            filename (str, optional): Путь к файлу. По умолчанию None.
        """
        try:
            # Если файл не указан, показываем диалог выбора файла
            if not filename:
                filename, _ = QFileDialog.getOpenFileName(
                    self,
                    "Выберите файл похода",
                    "",  # Начальная директория
                    "Файлы походов (*.json);;Все файлы (*.*)"
                )
            
            # Если файл выбран
            if filename:
                # Проверяем существование файла
                if not os.path.exists(filename):
                    QMessageBox.critical(self, "Ошибка", f"Файл не найден: {filename}")
                    return
                
                # Читаем и проверяем данные файла
                with open(filename, 'r', encoding='utf-8') as file:
                    try:
                        hike_data = json.load(file)
                        
                        # Проверяем структуру данных
                        required_fields = ['hike_name', 'participants', 'start_date', 
                                         'end_date', 'track_days', 'expenses_data']
                        if not all(field in hike_data for field in required_fields):
                            raise ValueError("Неверная структура файла")
                        
                        # Создаем виджет для работы с походом
                        self.main_works_widget = MainWorksWidget(hike_data, self)
                        self.setCentralWidget(self.main_works_widget)
                        
                        # Обновляем заголовок окна
                        self.current_file = filename
                        self.setWindowTitle(f"Калькулятор экспедиции - {os.path.basename(filename)}")
                        
                        # Активируем кнопки управления
                        self.save_action.setEnabled(True)
                        self.save_as_action.setEnabled(True)
                        self.close_action.setEnabled(True)
                        self.edit_trek_action.setEnabled(True)
                        self.stats_trek_action.setEnabled(True)
                        
                        # Обновляем список недавних файлов
                        if filename in self.recent_files:
                            self.recent_files.remove(filename)
                        self.recent_files.insert(0, filename)
                        if len(self.recent_files) > 5:
                            self.recent_files.pop()
                        self.save_recent_files()
                        self.populate_recent_files_menu()
                        
                    except json.JSONDecodeError:
                        QMessageBox.critical(self, "Ошибка", 
                                          "Файл содержит некорректные данные JSON")
                    except ValueError as e:
                        QMessageBox.critical(self, "Ошибка", str(e))
                        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{str(e)}")

    def save_hike(self):
        """
        Сохраняет текущий поход в файл.
        Если файл уже был открыт/сохранен ранее, использует тот же путь.
        Если это новый поход, вызывает диалог "Сохранить как".
        """
        if not self.current_file:
            return self.save_hike_as()
            
        try:
            hike_data = self.get_hike_data()
            if hike_data:
                with open(self.current_file, 'w', encoding='utf-8') as file:
                    json.dump(hike_data, file, ensure_ascii=False, indent=4)
                
                if hasattr(self, 'main_works_widget'):
                    self.main_works_widget.mark_as_saved()
                    
                return True
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {str(e)}")
            
        return False

    def save_hike_as(self):
        """
        Сохраняет текущий поход в новый файл.
        Предлагает имя файла на основе названия похода.
        """
        default_name = ""
        if hasattr(self, 'main_works_widget'):
            default_name = f"{self.main_works_widget.hike_data['hike_name']}.json"
        elif hasattr(self, 'create_hike_widget'):
            default_name = f"{self.create_hike_widget.hike_name.currentText()}.json"
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить поход как",
            default_name,  # Use trek name as default filename
            "JSON files (*.json)"
        )
        
        if filename:
            self.current_file = filename
            if self.save_hike():
                self.setWindowTitle(f"Калькулятор экспедиции - {os.path.basename(filename)}")
                return True
        return False

    def close_hike(self):
        """
        Закрывает текущий поход.
        Сбрасывает текущий выбранный файл, отключает действия сохранения и закрытия,
        устанавливает центральный виджет в пустое состояние.
        """
        self.current_file = None
        self.save_action.setEnabled(False)
        self.save_as_action.setEnabled(False)
        self.close_action.setEnabled(False)
        self.setCentralWidget(QWidget())
        self.main_layout = QVBoxLayout(self.centralWidget())
        self.saved_hikes_list = QListWidget()
        self.main_layout.addWidget(self.saved_hikes_list)
        self.show_empty_state()

    def create_and_save_hike(self, hike_name, hike_data):
        """
        Создаёт и сохраняет новый поход.
        Генерирует уникальное имя файла на основе hike_name, сохраняет данные по формату JSON,
        обновляет действия и список недавних файлов.
        """
        filename = self.get_unique_filename(hike_name + ".json")  # Добавляем расширение .json

        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(hike_data, file, ensure_ascii=False, indent=4)
        self.current_file = filename
        self.save_action.setEnabled(True)
        self.save_as_action.setEnabled(True)
        self.close_action.setEnabled(True)
        QMessageBox.information(self, "Создать новый поход",
                                f"Поход {hike_name} создан и сохранен как {filename}")

        # Обновление списка недавних файлов
        if filename in self.recent_files:
            self.recent_files.remove(filename)
        self.recent_files.insert(0, filename)
        if len(self.recent_files) > 5:
            self.recent_files.pop()
        self.save_recent_files()
        self.populate_recent_files_menu()

    def show_empty_state(self):
        """
        Отображает пустое состояние главного окна с темным фоном, центральной картинкой и кнопками.
        """
        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Устанавливаем более темный фон
        self.centralWidget().setStyleSheet("background-color: #4A4A4A;")  # Darker gray
        
        # Создаем и настраиваем метку для изображения
        background_label = QLabel()
        pixmap = QPixmap("icon_background.png")
        scaled_pixmap = pixmap.scaled(200, 200, 
                                    Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)
        background_label.setPixmap(scaled_pixmap)
        background_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Создаем кнопки
        buttons_layout = QHBoxLayout()
        
        create_button = QPushButton("Создать новый поход")
        create_button.setMinimumWidth(150)
        create_button.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #777777;
            }
        """)
        create_button.clicked.connect(self.show_create_hike_screen)
        
        open_button = QPushButton("Открыть поход")
        open_button.setMinimumWidth(150)
        open_button.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #777777;
            }
        """)
        open_button.clicked.connect(self.open_hike)
        
        buttons_layout.addWidget(create_button)
        buttons_layout.addWidget(open_button)
        
        # Добавляем элементы в макет
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(background_label)
        self.main_layout.addSpacing(20)  # Отступ между картинкой и кнопками
        self.main_layout.addLayout(buttons_layout)
        self.main_layout.addStretch(1)

class MainWindow(QMainWindow):
    def __init__(self):
        """
        Конструктор главного окна приложения.
        Устанавливает заголовок, иконку, размер окна, и инициализирует настройки и недавние файлы.
        Затем загружает пользовательский интерфейс.
        """
        super().__init__()
        self.setWindowTitle("Калькулятор экспедиции")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon("icon.png"))
        self.current_file = None
        self.settings = configparser.ConfigParser()
        
        # Проверка наличия файла init.ini, если отсутствует, создаётся дефолтный
        if not os.path.exists('init.ini'):
            self.create_default_ini()
        
        self.settings.read('init.ini', encoding='utf-8')
        self.recent_files = self.get_recent_files()
        self.init_ui()

    def create_default_ini(self):
        """
        Создаёт файл init.ini по умолчанию с пустым списком недавних файлов.
        Метод вызывается, если файл настроек не найден.
        """
        self.settings['Recent Files'] = {'files': '[]'}
        self.save_ini_file()

    def init_ui(self):
        """
        Инициализирует пользовательский интерфейс главного окна.
        Создаёт центральный виджет, меню, панель сохранённых походов и отображает начальное пустое состояние.
        """
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)

        # Создание строки меню
        menubar = self.menuBar()

        # Меню "Файл"
        file_menu = menubar.addMenu('Файл')
        
        new_hike_action = file_menu.addAction('Создать новый поход')
        new_hike_action.triggered.connect(self.show_create_hike_screen)
        
        open_action = file_menu.addAction('Открыть')
        open_action.triggered.connect(self.open_hike)
        
        self.save_action = file_menu.addAction('Сохранить')
        self.save_action.triggered.connect(self.save_hike)
        self.save_action.setEnabled(False)
        
        self.save_as_action = file_menu.addAction('Сохранить как...')
        self.save_as_action.triggered.connect(self.save_hike_as)
        self.save_as_action.setEnabled(False)
        
        self.close_action = file_menu.addAction('Закрыть')
        self.close_action.triggered.connect(self.close_hike)
        self.close_action.setEnabled(False)
        
        exit_action = file_menu.addAction('Выйти из программы')
        exit_action.triggered.connect(self.close)
        
        # Меню недавних файлов
        self.recent_files_menu = QMenu('Предыдущие файлы', self)
        self.populate_recent_files_menu()
        file_menu.addMenu(self.recent_files_menu)
        
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        
        # Меню "Вид"
        view_menu = menubar.addMenu('Вид')
        
        # Добавляем инструменты в меню "Вид"
        self.edit_trek_action = view_menu.addAction('Редактирование трека')
        self.edit_trek_action.triggered.connect(self.show_edit_trek)
        self.edit_trek_action.setEnabled(False)  # Initially disabled
        
        self.stats_trek_action = view_menu.addAction('Статистика трека')
        self.stats_trek_action.triggered.connect(self.show_trek_stats)
        self.stats_trek_action.setEnabled(False)  # Initially disabled

        # Меню "Настройки"
        settings_menu = menubar.addMenu('Настройки')
        settings_action = settings_menu.addAction('Настройки')
        settings_action.triggered.connect(self.show_settings)
        
        # Меню "Справка"
        help_menu = menubar.addMenu('Справка')
        about_action = help_menu.addAction('О программе')
        about_action.triggered.connect(self.show_about)
        website_action = help_menu.addAction('Перейти на вебсайт')
        website_action.triggered.connect(self.open_website)

        # Инициализация списка сохранённых походов
        self.saved_hikes_list = QListWidget()
        self.main_layout.addWidget(self.saved_hikes_list)

        # Отображение начального пустого состояния с фоновой картинкой
        self.show_empty_state()

    def show_empty_state(self):
        """
        Отображает пустое состояние главного окна с темным фоном, центральной картинкой и кнопками.
        """
        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Устанавливаем более темный фон
        self.centralWidget().setStyleSheet("background-color: #4A4A4A;")  # Darker gray
        
        # Создаем и настраиваем метку для изображения
        background_label = QLabel()
        pixmap = QPixmap("icon_background.png")
        scaled_pixmap = pixmap.scaled(200, 200, 
                                    Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)
        background_label.setPixmap(scaled_pixmap)
        background_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Создаем кнопки
        buttons_layout = QHBoxLayout()
        
        create_button = QPushButton("Создать новый поход")
        create_button.setMinimumWidth(150)
        create_button.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #777777;
            }
        """)
        create_button.clicked.connect(self.show_create_hike_screen)
        
        open_button = QPushButton("Открыть поход")
        open_button.setMinimumWidth(150)
        open_button.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #777777;
            }
        """)
        open_button.clicked.connect(self.open_hike)
        
        buttons_layout.addWidget(create_button)
        buttons_layout.addWidget(open_button)
        
        # Добавляем элементы в макет
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(background_label)
        self.main_layout.addSpacing(20)  # Отступ между картинкой и кнопками
        self.main_layout.addLayout(buttons_layout)
        self.main_layout.addStretch(1)

    def show_create_hike_screen(self):
        """
        Отображает экран создания нового похода.
        Создаёт виджет AddExpeditionWidget и устанавливает его как центральный для главного окна.
        """
        self.create_hike_widget = AddExpeditionWidget(self)
        self.setCentralWidget(self.create_hike_widget)

    def load_saved_hikes(self):
        """
        Загружает список сохранённых походов из файла saved_hikes.json и отображает их в списке.
        Если файл существует, считывает данные и добавляет каждый поход в QListWidget.
        """
        if os.path.exists("saved_hikes.json"):
            with open("saved_hikes.json", "r", encoding='utf-8') as file:
                hikes = json.load(file)
                for hike in hikes:
                    self.saved_hikes_list.addItem(hike)

    def show_settings(self):
        """
        Отображает окно настроек.
        Выводит информационное сообщение (в дальнейшем можно заменить на полноценный диалог настроек).
        """
        QMessageBox.information(self, "Настройки", "Настройки")

    def show_about(self):
        """
        Отображает информацию о программе.
        Всплывающее окно содержит информацию о разработчике и версии.
        """
        about_text = """
        Калькулятор экспедиции

        Разработчик: Горный клуб HIMALTREX
        Версия: 0.1 alfa

        Программа для учета расходов
        в туристических экспедициях
        """
        QMessageBox.about(self, "О программе", about_text)

    def open_website(self):
        """
        Открывает вебсайт проекта в браузере по заданному URL.
        """
        QDesktopServices.openUrl(QUrl("http://www.himaltrex.ru"))

    def get_recent_files(self):
        """
        Получает список недавних файлов из настроек.
        Если раздел 'Recent Files' существует, возвращает список из JSON строки, иначе возвращает пустой список.
        """
        if 'Recent Files' in self.settings:
            files = json.loads(self.settings['Recent Files'].get('files', '[]'))
            return files
        return []

    def populate_recent_files_menu(self):
        """
        Заполняет меню недавних файлов.
        Очищает текущее меню, проверяет наличие файла в списке и добавляет их как действия.
        Если список пуст, отключает меню.
        """
        self.recent_files_menu.clear()
        if not self.recent_files:
            self.recent_files_menu.setEnabled(False)
        else:
            self.recent_files_menu.setEnabled(True)
            for f in self.recent_files:
                action = self.recent_files_menu.addAction(f)
                action.triggered.connect(lambda checked, filename=f: self.open_recent_file(filename))

    def open_recent_file(self, filename):
        """
        Открывает выбранный недавний файл.
        Если файл существует, вызывает open_hike; если нет, выводит предупреждение и обновляет список.
        
        :param filename: Путь к файлу
        """
        if os.path.exists(filename):
            self.open_hike(filename)
        else:
            QMessageBox.warning(self, "Ошибка", f"Файл {filename} не найден.")
            self.recent_files.remove(filename)
            self.save_recent_files()
            self.populate_recent_files_menu()

    def save_recent_files(self):
        """
        Сохраняет текущий список недавних файлов в настройки и записывает их в init.ini.
        """
        self.settings['Recent Files'] = {'files': json.dumps(self.recent_files)}
        self.save_ini_file()

    def save_ini_file(self):
        """
        Записывает настройки в файл init.ini с использованием кодировки UTF-8.
        """
        with open('init.ini', 'w', encoding='utf-8') as configfile:
            self.settings.write(configfile)

    def open_hike(self, filename=None):
        """
        Открывает файл с данными похода.
        Показывает диалог выбора файла, загружает данные и обновляет интерфейс.
        
        Args:
            filename (str, optional): Путь к файлу. По умолчанию None.
        """
        try:
            # Если файл не указан, показываем диалог выбора файла
            if not filename:
                filename, _ = QFileDialog.getOpenFileName(
                    self,
                    "Выберите файл похода",
                    "",  # Начальная директория
                    "Файлы походов (*.json);;Все файлы (*.*)"
                )
            
            # Если файл выбран
            if filename:
                # Проверяем существование файла
                if not os.path.exists(filename):
                    QMessageBox.critical(self, "Ошибка", f"Файл не найден: {filename}")
                    return
                
                # Читаем и проверяем данные файла
                with open(filename, 'r', encoding='utf-8') as файл:
                    try:
                        hike_data = json.load(file)
                        
                        # Проверяем структуру данных
                        required_fields = ['hike_name', 'participants', 'start_date', 
                                         'end_date', 'track_days', 'expenses_data']
                        if not all(field in hike_data for field in required_fields):
                            raise ValueError("Неверная структура файла")
                        
                        # Создаем виджет для работы с походом
                        self.main_works_widget = MainWorksWidget(hike_data, self)
                        self.setCentralWidget(self.main_works_widget)
                        
                        # Обновляем заголовок окна
                        self.current_file = filename
                        self.setWindowTitle(f"Калькулятор экспедиции - {os.path.basename(filename)}")
                        
                        # Активируем кнопки управления
                        self.save_action.setEnabled(True)
                        self.save_as_action.setEnabled(True)
                        self.close_action.setEnabled(True)
                        self.edit_trek_action.setEnabled(True)
                        self.stats_trek_action.setEnabled(True)
                        
                        # Обновляем список недавних файлов
                        if filename in self.recent_files:
                            self.recent_files.remove(filename)
                        self.recent_files.insert(0, filename)
                        if len(self.recent_files) > 5:
                            self.recent_files.pop()
                        self.save_recent_files()
                        self.populate_recent_files_menu()
                        
                    except json.JSONDecodeError:
                        QMessageBox.critical(self, "Ошибка", 
                                          "Файл содержит некорректные данные JSON")
                    except ValueError as e:
                        QMessageBox.critical(self, "Ошибка", str(e))
                        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{str(e)}")

    def save_hike(self):
        """
        Сохраняет текущий поход в файл.
        Если файл уже был открыт/сохранен ранее, использует тот же путь.
        Если это новый поход, вызывает диалог "Сохранить как".
        """
        if not self.current_file:
            return self.save_hike_as()
            
        try:
            hike_data = self.get_hike_data()
            if hike_data:
                with open(self.current_file, 'w', encoding='utf-8') as файл:
                    json.dump(hike_data, file, ensure_ascii=False, indent=4)
                
                if hasattr(self, 'main_works_widget'):
                    self.main_works_widget.mark_as_saved()
                    
                return True
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {str(e)}")
            
        return False

    def save_hike_as(self):
        """
        Сохраняет текущий поход в новый файл.
        """
        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить поход как", "", "JSON files (*.json)")
        if filename:
            self.current_file = filename
            if self.save_hike():
                self.setWindowTitle(f"Калькулятор экспедиции - {os.path.basename(filename)}")
                return True
        return False

    def close_hike(self):
        """
        Закрывает текущий поход.
        Сбрасывает текущий выбранный файл, отключает действия сохранения и закрытия,
        устанавливает центральный виджет в пустое состояние.
        """
        self.current_file = None
        self.save_action.setEnabled(False)
        self.save_as_action.setEnabled(False)
        self.close_action.setEnabled(False)
        self.setCentralWidget(QWidget())
        self.main_layout = QVBoxLayout(self.centralWidget())
        self.saved_hikes_list = QListWidget()
        self.main_layout.addWidget(self.saved_hikes_list)
        self.show_empty_state()

    def show_main_works_widget(self, hike_data):
        """
        Отображает основной виджет работы с данными похода (MainWorksWidget).
        Устанавливает его как центральный виджет главного окна.
        
        :param hike_data: Словарь с данными о походе
        """
        self.main_works_widget = MainWorksWidget(hike_data, self)
        self.setCentralWidget(self.main_works_widget)
        # Enable view menu actions when trek is loaded
        self.edit_trek_action.setEnabled(True)
        self.stats_trek_action.setEnabled(True)

    def get_hike_data(self):
        """
        Получает данные текущего похода для сохранения.
        Формирует словарь с именем похода, участниками, датами, днями трека и расходами.
        """
        if hasattr(self, 'main_works_widget'):
            # Get expenses data from table
            expenses_data = []
            num_participants = len(self.main_works_widget.hike_data['participants'])
            num_days = self.main_works_widget.hike_data['track_days']
            
            for строки in range(num_days):  # Exclude total row
                day_expenses = []
                for col in range(1, num_participants + 1):  # Skip date column
                    item = self.main_works_widget.table.item(row, col)
                    expense = item.text() if item else "0"
                    day_expenses.append(expense)
                expenses_data.append(day_expenses)

            return {
                "hike_name": self.main_works_widget.hike_data['hike_name'],
                "participants": self.main_works_widget.hike_data['participants'],
                "start_date": self.main_works_widget.hike_data['start_date'],
                "end_date": self.main_works_widget.hike_data['end_date'],
                "track_days": self.main_works_widget.hike_data['track_days'],
                "expenses_data": expenses_data
            }
        elif hasattr(self, 'create_hike_widget'):
            num_participants = self.create_hike_widget.participant_fields.count()
            num_days = self.create_hike_widget.track_days.value()
            
            # Create initial expenses array filled with zeros
            expenses_data = [["0"] * num_participants for _ in range(num_days)]
            
            return {
                "hike_name": self.create_hike_widget.hike_name.currentText(),
                "participants": [
                    {
                        "name": self.create_hike_widget.participant_fields.itemAt(i).layout().itemAt(0).widget().text() or f"Участник {i + 1}",
                        "payment": self.create_hike_widget.participant_fields.itemAt(i).layout().itemAt(1).widget().value()
                    }
                    for i in range(num_participants)
                ],
                "start_date": self.create_hike_widget.start_date.date().toString(Qt.DateFormat.ISODate),
                "end_date": self.create_hike_widget.end_date.date().toString(Qt.DateFormat.ISODate),
                "track_days": num_days,
                "expenses_data": expenses_data
            }
        else:
            QMessageBox.warning(self, "Ошибка", "Нет активного похода для сохранения")
            return None

    def show_edit_trek(self):
        """
        Показывает экран редактирования трека.
        Создает новый экземпляр MainWorksWidget если необходимо.
        """
        if hasattr(self, 'main_works_widget'):
            # Recreate MainWorksWidget with current data
            self.main_works_widget = MainWorksWidget(self.main_works_widget.hike_data, self)
            self.setCentralWidget(self.main_works_widget)
            self.main_works_widget.has_unsaved_changes = False

    def show_trek_stats(self):
        """
        Показывает экран статистики трека.
        Создает новый экземпляр StatisticWidget с текущими данными.
        """
        if hasattr(self, 'main_works_widget'):
            from statistic import StatisticWidget
            # Get current data before switching
            current_data = self.get_hike_data()
            statistic_widget = StatisticWidget(current_data, 
                                             self.main_works_widget.table, 
                                             self)
            self.setCentralWidget(statistic_widget)

def main():
    """
    Точка входа в приложение.
    Создаёт экземпляр QApplication, главное окно и запускает главный цикл событий.
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()