from PyQt6.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, 
                           QLabel, QHeaderView, QHBoxLayout)
from PyQt6.QtCore import Qt

class StatisticWidget(QWidget):
    def __init__(self, hike_data, table_data, parent=None):
        super().__init__(parent)
        self.hike_data = hike_data
        self.table_data = table_data
        self.setWindowTitle(f"Статистика похода: {self.hike_data['hike_name']}")
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.setStyleSheet("background-color: #4A4A4A; color: white;")
        
        # Header with trek name
        header_text = f"<h2>Статистика похода: {self.hike_data['hike_name']}</h2>"
        header_label = QLabel(header_text)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setStyleSheet("color: white;")
        self.main_layout.addWidget(header_label)

        # Create and configure table
        num_rows = self.table_data.rowCount()
        num_cols = self.table_data.columnCount()
        self.table = QTableWidget(num_rows, num_cols)
        
        # Get header labels safely
        header_labels = ["Дата"]  # First column is always "Дата"
        for i in range(1, num_cols):
            header_item = self.table_data.horizontalHeaderItem(i)
            if header_item:
                header_labels.append(header_item.text())
            else:
                header_labels.append(f"Участник {i}")
        
        self.table.setHorizontalHeaderLabels(header_labels)
        
        # Copy data and make cells read-only
        for col in range(num_cols):
            for row in range(num_rows):
                original_item = self.table_data.item(row, col)
                if original_item:
                    new_item = QTableWidgetItem(original_item.text())
                    new_item.setFlags(new_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    new_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | 
                                           Qt.AlignmentFlag.AlignVCenter)
                    new_item.setForeground(Qt.GlobalColor.white)
                    self.table.setItem(row, col, new_item)

        # Style the table for dark theme
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #333333;
                color: white;
                gridline-color: #666666;
            }
            QHeaderView::section {
                background-color: #4A4A4A;
                color: white;
                border: 1px solid #666666;
            }
            QTableWidget::item {
                border: 1px solid #666666;
            }
        """)

        # Configure table properties
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        for i in range(1, num_cols):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        
        self.main_layout.addWidget(self.table)

        # Initialize arrays for statistics
        num_participants = len(self.hike_data['participants'])
        participant_expenses = [0] * num_participants
        participant_initial = [p['payment'] for p in self.hike_data['participants']]

        # Calculate total expenses from expenses_data
        for day_idx, day_expenses in enumerate(self.hike_data['expenses_data']):
            for participant_idx, expense in enumerate(day_expenses):
                try:
                    participant_expenses[participant_idx] += float(expense)
                except ValueError:
                    pass

        # Create layout for participant statistics columns
        stats_layout = QHBoxLayout()
        
        # Calculate and show statistics for each participant
        for col in range(1, num_cols - 1):
            participant_idx = col - 1
            participant_name = self.table_data.horizontalHeaderItem(col).text()
            initial_amount = participant_initial[participant_idx]
            total_expenses = abs(participant_expenses[participant_idx])
            days_count = self.hike_data['track_days']
            daily_average = total_expenses / days_count if days_count > 0 else 0
            
            # Calculate final balance: initial payment - total expenses
            final_balance = initial_amount + participant_expenses[participant_idx]
            
            # Create frame for participant statistics
            participant_stats = QLabel(
                f"<div style='background-color: #333333; padding: 10px; margin: 5px; "
                f"border-radius: 5px; min-width: 200px;'>"
                f"<h4 style='text-align: center; color: white;'>{participant_name}</h4>"
                f"<hr style='border-color: #666666;'>"
                f"<p style='color: white;'>Внесено в общак: {initial_amount:.0f}</p>"
                f"<p style='color: white;'>Общие расходы: {total_expenses:.0f}</p>"
                f"<p style='color: white;'>Расход в день: {daily_average:.0f}</p>"
                f"<p style='color: white;'>Баланс: {final_balance:.0f}</p>"
                f"</div>"
            )
            
            stats_layout.addWidget(participant_stats)
        
        # Add statistics layout to main layout
        stats_container = QWidget()
        stats_container.setLayout(stats_layout)
        stats_container.setStyleSheet("background-color: #4A4A4A;")
        self.main_layout.addWidget(stats_container)

    def _get_return_message(self, amount):
        """Helper method to generate return/pay message"""
        if amount > 0:
            return f"К возврату: {amount:.0f}"
        elif amount < 0:
            return f"Необходимо досдать в общак: {abs(amount)::.0f}"
        return "Баланс нулевой"

    def _parse_number(self, text):
        """Helper method to convert string numbers with spaces to float"""
        try:
            return float(text.replace(" ", ""))
        except (ValueError, AttributeError):
            return 0.0