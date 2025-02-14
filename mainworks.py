from PyQt6.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QDialog, 
                             QFormLayout, QLineEdit, QLabel, QHeaderView, QRadioButton, QButtonGroup, 
                             QGroupBox, QDialogButtonBox, QMessageBox, QPushButton)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon
# Add to imports in mainworks.py
from statistic import StatisticWidget

class ExpenseDialog(QDialog):
    def __init__(self, parent=None):
        """
        Конструктор диалогового окна для ввода расходов или пополнения.
        Инициализирует окно и задаёт заголовок.
        """
        super().__init__(parent)
        self.setWindowTitle("Ввод расходов / пополнения")
        self.setup_ui()

    def setup_ui(self):
        """
        Настраивает пользовательский интерфейс диалогового окна.
        Создаёт форму с радиокнопками для выбора категории расходов (Завтрак, Ланч, Обед, Пополнение),
        поле для ввода суммы и стандартные кнопки Ok/Cancel.
        """
        layout = QFormLayout(self)
        # Создаем группу с радиокнопками для выбора раздела расходов
        group_box = QGroupBox("Выберите раздел")
        radio_layout = QVBoxLayout(group_box)
        self.button_group = QButtonGroup(self)
        self.radio_breakfast = QRadioButton("Завтрак")
        self.radio_lunch = QRadioButton("Ланч")
        self.radio_dinner = QRadioButton("Обед")
        self.radio_topup = QRadioButton("Пополнение")
        self.button_group.addButton(self.radio_breakfast)
        self.button_group.addButton(self.radio_lunch)
        self.button_group.addButton(self.radio_dinner)
        self.button_group.addButton(self.radio_topup)
        self.radio_breakfast.setChecked(True)
        radio_layout.addWidget(self.radio_breakfast)
        radio_layout.addWidget(self.radio_lunch)
        radio_layout.addWidget(self.radio_dinner)
        radio_layout.addWidget(self.radio_topup)
        layout.addRow(group_box)
        
        # Поле для ввода суммы
        self.amount_edit = QLineEdit(self)
        self.amount_edit.setPlaceholderText("Введите сумму")
        layout.addRow("Сумма:", self.amount_edit)
        
        # Диалоговые кнопки Ok и Cancel
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                          QDialogButtonBox.StandardButton.Cancel, 
                                          parent=self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

    def get_values(self):
        """
        Возвращает выбранную категорию, введенную сумму и знак операции.
        Если выбрана категория "Пополнение", знак будет "+",
        для остальных категорий знак "-".
        Возвращает кортеж: (category, amount, sign).
        """
        if self.radio_topup.isChecked():
            category = "Пополнение"
            sign = "+"
        elif self.radio_breakfast.isChecked():
            category = "Завтрак"
            sign = "-"
        elif self.radio_lunch.isChecked():
            category = "Ланч"
            sign = "-"
        elif self.radio_dinner.isChecked():
            category = "Обед"
            sign = "-"
        else:
            category = ""
            sign = ""
        try:
            amount_val = float(self.amount_edit.text().strip())
        except ValueError:
            amount_val = 0.0
        return category, amount_val, sign

class MainWorksWidget(QWidget):
    def __init__(self, hike_data, parent=None):
        """
        Конструктор главного виджета для работы с данными похода.
        """
        super().__init__(parent)
        self.hike_data = hike_data
        self.setWindowTitle(f"Поход: {self.hike_data['hike_name']}")
        self.setWindowIcon(QIcon("icon.png"))
        self.has_unsaved_changes = False
        
        # Initialize or validate expenses_data
        num_participants = len(self.hike_data['participants'])
        num_days = self.hike_data['track_days']
        
        # Create new expenses_data if not present or wrong size
        if ('expenses_data' not in self.hike_data or 
            len(self.hike_data['expenses_data']) != num_days or 
            any(len(day) != num_participants for day in self.hike_data['expenses_data'])):
            
            self.hike_data['expenses_data'] = [
                ["0" for _ in range(num_participants)] 
                for _ in range(num_days)
            ]
        
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        # Header layout with trek name and dates
        header_layout = QHBoxLayout()
        
        # Trek info label (name and dates) with participant count on new line
        participant_count = len(self.hike_data.get('participants', [])) - 1  # Subtract 1 to exclude "Общак"
        info_text = (f"<h2>{self.hike_data.get('hike_name', 'Без названия')} | "
                    f"{QDate.fromString(self.hike_data.get('start_date', ''), Qt.DateFormat.ISODate).toString('dd.MM.yyyy')} - "
                    f"{QDate.fromString(self.hike_data.get('end_date', ''), Qt.DateFormat.ISODate).toString('dd.MM.yyyy')}</h2>"
                    f"<h3>Количество участников: {participant_count}</h3>")
        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        header_layout.addWidget(info_label)
        
        # Finish trek button
        finish_button = QPushButton("Завершить трек")
        finish_button.clicked.connect(self.finish_trek)
        header_layout.addWidget(finish_button, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.main_layout.addLayout(header_layout)
        
        # Remove bank info label initialization
        self.initial_payments = [p['payment'] for p in self.hike_data.get('participants', [])]
        self.total_bank_amount = sum(self.initial_payments)
        
        # Определение количества дней похода
        self.start_date = QDate.fromString(self.hike_data.get('start_date', ""), Qt.DateFormat.ISODate) if self.hike_data.get('start_date') else QDate.currentDate()
        self.end_date = QDate.fromString(self.hike_data.get('end_date', ""), Qt.DateFormat.ISODate) if self.hike_data.get('end_date') else QDate.currentDate()
        self.days = self.start_date.daysTo(self.end_date) + 1
        
        # Создание таблицы: строки для каждого дня похода + строка "Итого"
        # Количество столбцов: 1 (Дата) + количество участников
        num_participants = len(self.hike_data.get('participants', []))
        num_cols = num_participants + 1  # +1 for Date column
        header_labels = ["Дата"] + [p['name'] for p in self.hike_data.get('participants', []) if p['name'] != "Общак"]
        self.table = QTableWidget(self.days + 1, num_cols)
        self.table.setHorizontalHeaderLabels(header_labels)
        
        # Настройка размеров заголовков таблицы
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        for i in range(1, num_cols):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        
        # Заполнение ячеек таблицы
        for row in range(self.days):
            date = self.start_date.addDays(row)
            self.table.setItem(row, 0, QTableWidgetItem(date.toString("dd.MM.yyyy")))
            # Заполнение ячеек для участников
            for col in range(1, num_cols):
                item = QTableWidgetItem("0")
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, col, item)
        
        # Заполнение строки "Итого"
        self.table.setItem(self.days, 0, QTableWidgetItem("Итого"))
        # Итоги для каждого участника
        for col in range(1, num_cols):
            item = QTableWidgetItem(self.format_money(self.initial_payments[col-1], integer=True))
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(self.days, col, item)
        
        self.main_layout.addWidget(self.table)
        # Обработка двойного клика по ячейке для ввода или редактирования расходов
        self.table.cellDoubleClicked.connect(self.edit_expense)
        
        # Configure table properties for automatic row height adjustment
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.setWordWrap(True)
        
        # Make "Итого" row read-only and set its style
        for col in range(num_cols):
            item = self.table.item(self.days, col)
            if item:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                font = item.font()
                font.setBold(True)
                item.setFont(font)

    def format_money(self, value, integer=False):
        """
        Форматирует число для отображения денег.
        Добавляет пробел в качестве разделителя тысяч.
        Если integer=True, округляет число до целого и не показывает десятичную часть.
        
        :param value: Числовое значение для форматирования.
        :param integer: Флаг для отображения без десятичных знаков.
        :return: Отформатированное строковое представление числа.
        """
        if integer:
            s = format(round(value), ",")
        else:
            s = format(value, ",.2f")
        return s.replace(",", " ")

    def edit_expense(self, row, col):
        """
        Обрабатывает редактирование расходов при двойном клике по ячейке таблицы.
        """
        if col == 0 or row >= self.days:
            return
                
        dialog = ExpenseDialog(self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            category, amount, sign = dialog.get_values()
            actual_amount = amount if sign == "+" else -amount
            
            # Update individual participant expense
            participant_idx = col - 1
            try:
                current_amount = float(self.hike_data['expenses_data'][row][participant_idx])
                new_amount = current_amount + actual_amount
                self.hike_data['expenses_data'][row][participant_idx] = str(new_amount)
            except (ValueError, IndexError):
                self.hike_data['expenses_data'][row][participant_idx] = str(actual_amount)
            
            # Update table cell
            self._update_table_cell(row, col, category, amount, sign)
            
            self.recalculate_totals()
            self.mark_as_modified()

    def _update_table_cell(self, row, col, category, amount, sign):
        """
        Вспомогательный метод для обновления ячейки таблицы.
        """
        cell = self.table.item(row, col)
        current_text = cell.text().strip() if cell and cell.text().strip() != "0" else ""
        entries = [s.strip() for s in current_text.split(";")] if current_text else []
        new_entry = f"{category} {sign}{round(amount)}"
        entries.append(new_entry)
        cell_item = QTableWidgetItem("; ".join(entries))
        cell_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, col, cell_item)

    def recalculate_totals(self):
        num_cols = self.table.columnCount()
        participant_totals = self.initial_payments.copy()
        warning_messages = []
        
        # Remove any existing warning labels
        for i in reversed(range(self.main_layout.count())):
            widget = self.main_layout.itemAt(i).widget()
            if isinstance(widget, QLabel) and widget.property("warning"):
                widget.deleteLater()
        
        for col in range(1, num_cols - 1):
            for row in range(self.days):
                cell_item = self.table.item(row, col)
                if cell_item:
                    text = cell_item.text().strip()
                    if text != "0" and text:
                        entries = [e.strip() for e in text.split(";") if e.strip()]
                        for entry in entries:
                            parts = entry.split()
                            if len(parts) == 2:
                                try:
                                    value = float(parts[1])
                                    participant_totals[col-1] += value
                                except ValueError:
                                    pass

        # Update totals row with modified coloring scheme
        for col in range(1, num_cols - 1):
            total = participant_totals[col-1]
            formatted_total = str(round(total))
            total_item = QTableWidgetItem(formatted_total)
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            total_item.setData(Qt.ItemDataRole.UserRole, total)
            total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make read-only
            
            if total < 0:
                total_item.setBackground(Qt.GlobalColor.darkRed)
                total_item.setForeground(Qt.GlobalColor.white)  # White text for dark red background
                participant_name = self.table.horizontalHeaderItem(col).text()
                warning_messages.append(f"Участник {participant_name}: Внесите деньги!")
            elif total < 1000:
                total_item.setBackground(Qt.GlobalColor.yellow)
                total_item.setForeground(Qt.GlobalColor.black)  # Black text for yellow background
            
            self.table.setItem(self.days, col, total_item)

        # Make "Общак" total cell read-only too
        common_total = sum(participant_totals)
        common_total_item = QTableWidgetItem(str(round(common_total)))
        common_total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        common_total_item.setData(Qt.ItemDataRole.UserRole, common_total)
        common_total_item.setFlags(common_total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(self.days, num_cols - 1, common_total_item)

        # Display warning messages if any
        if warning_messages:
            warning_label = QLabel("\n".join(warning_messages))
            warning_label.setStyleSheet("color: darkRed;")
            warning_label.setProperty("warning", True)  # Mark as warning label
            warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.main_layout.addWidget(warning_label)

    def mark_as_modified(self):
        """
        Помечает документ как измененный и обновляет заголовок окна.
        Активирует пункты меню для сохранения файла.
        """
        if not self.has_unsaved_changes:
            self.has_unsaved_changes = True
            current_title = self.parent().windowTitle()
            if not current_title.endswith('*'):
                self.parent().setWindowTitle(f"{current_title}*")
            
            # Enable save actions in parent window
            if hasattr(self.parent(), "save_action"):
                self.parent().save_action.setEnabled(True)
            if hasattr(self.parent(), "save_as_action"):
                self.parent().save_as_action.setEnabled(True)

    def mark_as_saved(self):
        """
        Помечает документ как сохраненный и обновляет заголовок окна.
        """
        self.has_unsaved_changes = False
        current_title = self.parent().windowTitle()
        if current_title.endswith('*'):
            self.parent().setWindowTitle(current_title[:-1])
            self.parent().save_action.setEnabled(False)

    def finish_trek(self):
        """
        Обработчик нажатия кнопки "Завершить трек". 
        Форматирует числа без пробелов и открывает окно статистики.
        """
        # Remove spaces from numbers before showing statistics
        num_cols = self.table.columnCount()
        for row in range(self.days + 1):  # Include "Итого" row
            for col in range(1, num_cols):  # Skip date column
                cell = self.table.item(row, col)
                if cell:
                    text = cell.text()
                    if text != "0":
                        # Process each entry in the cell
                        entries = [e.strip() for e in text.split(";") if e.strip()]
                        formatted_entries = []
                        for entry in entries:
                            parts = entry.split()
                            if len(parts) >= 2:
                                # Remove spaces from numbers
                                number = parts[-1].replace(" ", "")
                                formatted_entry = f"{' '.join(parts[:-1])} {number}"
                                formatted_entries.append(formatted_entry)
                        
                        cell.setText("; ".join(formatted_entries))

        from statistic import StatisticWidget
        statistic_widget = StatisticWidget(self.hike_data, self.table, self)
        self.parent().setCentralWidget(statistic_widget)