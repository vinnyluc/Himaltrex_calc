import json, os
from PyQt6.QtWidgets import (QWidget, QFormLayout, QComboBox, QSpinBox, 
                          QVBoxLayout, QLineEdit, QDateEdit, QPushButton, 
                          QMessageBox, QHBoxLayout, QLabel)
from PyQt6.QtCore import Qt, QDate

class AddExpeditionWidget(QWidget):
    def __init__(self, parent=None):
        """
        Конструктор виджета добавления похода.
        Инициализирует родителя и запускает построение UI.
        """
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        """
        Инициализирует и настраивает элементы пользовательского интерфейса.
        Создаёт поля для ввода названия похода, количества участников, дат, длительности.
        """
        layout = QFormLayout(self)

        # Настройка выпадающего списка с названиями походов и длительностями по умолчанию
        self.hike_name = QComboBox()
        self.treks = {
            "Аннапурна": 16,
            "Верхний Мустанг": 10,
            "Госайкунда": 7,
            "Канченджанга": 20,
            "Лангтанг": 10,
            "Манаслу": 18,
            "Марди Химал": 5,
            "Тибет": 15,
            "Эверест": 12,
            "Знакомство с Непалом": 12
        }
        for trek in sorted(self.treks.keys()):
            self.hike_name.addItem(trek)

        # Настройка обработчика изменения названия похода
        self.hike_name.currentTextChanged.connect(self.update_default_days)
        
        # Настройка поля количества участников
        self.participant_count = QSpinBox()
        self.participant_count.setValue(1)
        self.participant_count.valueChanged.connect(self.update_participant_fields)
        
        # Создание контейнера для полей участников
        self.participant_fields = QVBoxLayout()
        self.update_participant_fields()
        
        # Настройка полей дат и длительности
        self.start_date = QDateEdit()
        self.end_date = QDateEdit()
        self.track_days = QSpinBox()
        self.track_days.setValue(self.treks[self.hike_name.currentText()])
        self.track_days.valueChanged.connect(self.update_end_date)
        
        # Установка начальных дат
        default_date = QDate(2025, 3, 20)
        self.start_date.setDate(default_date)
        self.end_date.setDate(default_date.addDays(self.track_days.value()))
        self.start_date.dateChanged.connect(self.update_end_date)
        
        # Создание разметки для кнопок
        buttons_layout = QHBoxLayout()
        
        # Создание кнопки "Создать поход"
        create_btn = QPushButton("Создать поход")
        create_btn.clicked.connect(self.create_hike)
        
        # Создание кнопки "Отмена"
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.cancel_creation)
        
        # Добавление кнопок в горизонтальную разметку
        buttons_layout.addWidget(create_btn)
        buttons_layout.addWidget(cancel_btn)

        # Добавление всех элементов в форму
        layout.addRow("Название похода:", self.hike_name)
        layout.addRow("Количество участников:", self.participant_count)
        layout.addRow("Имена участников:", self.participant_fields)
        layout.addRow("Дата начала:", self.start_date)
        layout.addRow("Длительность похода (дней):", self.track_days)
        layout.addRow("Дата окончания:", self.end_date)
        layout.addRow(buttons_layout)  # Add buttons layout instead of single button

    def update_participant_fields(self):
        """
        Обновляет поля для ввода информации об участниках.
        Сохраняет введённые ранее данные, очищает старые поля и создаёт новые в соответствии с количеством участников.
        Каждое поле состоит из строки для имени, спинбокса для суммы платежа и метки валюты.
        """
        # Сохраняем текущие данные участников, если они были введены
        current_data = []
        for i in range(self.participant_fields.count()):
            row_layout = self.participant_fields.itemAt(i)
            if row_layout and row_layout.layout():
                name_widget = row_layout.layout().itemAt(0).widget()
                payment_widget = row_layout.layout().itemAt(1).widget()
                if name_widget and payment_widget:
                    current_data.append({
                        "name": name_widget.text(),
                        "payment": payment_widget.value()
                    })
                else:
                    current_data.append(None)
            else:
                current_data.append(None)

        # Очистка существующих полей
        while self.participant_fields.count():
            item = self.participant_fields.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
            elif item and item.layout():
                # Очистка вложенных виджетов в layout
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                item.layout().deleteLater()

        # Создание новых полей на основе значения participant_count
        for i in range(self.participant_count.value()):
            # Создаем горизонтальный layout для строки участника
            participant_row = QHBoxLayout()

            # Создаем поле ввода имени участника
            participant_name = QLineEdit()
            participant_name.setPlaceholderText(f"Участник {i + 1}")
            participant_name.setMinimumWidth(200)

            # Создаем спинбокс для ввода суммы платежа
            participant_payment = QSpinBox()
            participant_payment.setMinimum(0)
            participant_payment.setMaximum(1000000)
            participant_payment.setSingleStep(1000)  # Шаг изменения значения — 1000

            # Создаем метку валюты
            currency_label = QLabel("рупий")

            # Восстанавливаем данные, если они уже были введены
            if i < len(current_data) and current_data[i]:
                participant_name.setText(current_data[i]["name"])
                participant_payment.setValue(current_data[i]["payment"])
            else:
                participant_payment.setValue(20000)  # Значение по умолчанию

            # Добавляем виджеты в строку
            participant_row.addWidget(participant_name)
            participant_row.addWidget(participant_payment)
            participant_row.addWidget(currency_label)

            # Добавляем строку в основной layout для участников
            self.participant_fields.addLayout(participant_row)

    def update_end_date(self):
        """
        Обновляет дату окончания похода.
        Вычисляет новую дату окончания на основе даты начала и длительности похода (в днях).
        """
        start_date = self.start_date.date()
        days = self.track_days.value()
        end_date = start_date.addDays(days)
        self.end_date.setDate(end_date)

    def update_default_days(self):
        """
        Обновляет значение длительности похода (track_days) в зависимости от выбранного названия похода.
        При изменении названия автоматически обновляет длительность и дату окончания.
        """
        trek_name = self.hike_name.currentText()
        self.track_days.setValue(self.treks[trek_name])
        self.update_end_date()

    def get_unique_filename(self, base_name):
        """
        Генерирует уникальное имя файла на основе базового имени.
        Если файл с таким именем уже существует, добавляет числовой суффикс.
        
        :param base_name: Базовое имя файла без расширения
        :return: Уникальное имя файла с расширением .json
        """
        filename = f"{base_name}.json"
        if not os.path.exists(filename):
            return filename
        
        counter = 1
        while True:
            filename = f"{base_name}{counter}.json"
            if not os.path.exists(filename):
                return filename
            counter += 1

    def create_hike(self):
        """
        Создаёт новый поход на основе введённых данных.
        Формирует структуру данных и массив расходов.
        """
        hike_name = self.hike_name.currentText()
        participants = []
        
        # Получение базовых параметров
        num_participants = self.participant_fields.count()
        num_days = self.track_days.value()
        
        # Создание массива расходов с учётом общака
        expenses_data = []
        for day in range(num_days):
            day_expenses = ["0"] * (num_participants + 1)  # +1 для общака
            expenses_data.append(day_expenses)
        
        # Сбор информации об участниках
        for i in range(num_participants):
            row_layout = self.participant_fields.itemAt(i)
            name_widget = row_layout.layout().itemAt(0).widget()
            payment_widget = row_layout.layout().itemAt(1).widget()
            
            name = name_widget.text() or f"Участник {i + 1}"
            payment = payment_widget.value()
            
            participants.append({
                "name": name,
                "payment": payment
            })
        
        # Добавление общака в список участников
        participants.append({
            "name": "Общак",
            "payment": 0
        })
        
        # Формирование итоговой структуры данных
        hike_data = {
            "hike_name": hike_name,
            "participants": participants,
            "start_date": self.start_date.date().toString(Qt.DateFormat.ISODate),
            "end_date": self.end_date.date().toString(Qt.DateFormat.ISODate),
            "track_days": num_days,
            "expenses_data": expenses_data
        }
        
        # Активация кнопок сохранения и закрытия
        if hasattr(self.parent, "save_action"):
            self.parent.save_action.setEnabled(True)
        if hasattr(self.parent, "save_as_action"):
            self.parent.save_as_action.setEnabled(True)
        if hasattr(self.parent, "close_action"):
            self.parent.close_action.setEnabled(True)
        
        # Обновление заголовка окна
        self.parent.setWindowTitle(f"Калькулятор экспедиции - {hike_name}")
        
        # Отображение основного виджета работы с походом
        self.parent.show_main_works_widget(hike_data)

    def cancel_creation(self):
        """
        Отменяет создание похода и возвращает в главное окно.
        """
        # Create new central widget and layout
        central_widget = QWidget()
        self.parent.setCentralWidget(central_widget)
        self.parent.main_layout = QVBoxLayout(central_widget)
        
        # Show empty state
        self.parent.show_empty_state()