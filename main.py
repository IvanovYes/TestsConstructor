
# main.py - Главный модуль системы КУТ

import sys
import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from config import config
from admin_auth import LoginDialog
from admin_mode import AdminWindow
from test_mode import TestLoginWindow

class MainWindow(QMainWindow):
    """Главное окно выбора режима"""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.setWindowTitle("Конструктор Учебных Тестов (КУТ)")
        self.setGeometry(300, 300, 600, 500)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("КОНСТРУКТОР УЧЕБНЫХ ТЕСТОВ")
        title.setStyleSheet("""
            font-size: 28px; 
            font-weight: bold; 
            color: #2c3e50;
            margin-bottom: 20px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Логотип
        logo = QLabel("🎓")
        logo.setStyleSheet("font-size: 120px;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        layout.addSpacing(30)

        # Описание
        description = QLabel(
            "Программная оболочка для создания, администрирования\n"
            "и прохождения учебных тестов"
        )
        description.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)

        layout.addSpacing(40)

        # Кнопки выбора режима
        admin_button = self.create_mode_button(
            "👨‍💼 Режим администратора",
            "Создание и редактирование тестов, просмотр результатов",
            "#3498db",
            self.open_admin_mode
        )

        test_button = self.create_mode_button(
            "🎯 Режим тестирования",
            "Прохождение учебных тестов",
            "#2ecc71",
            self.open_test_mode
        )

        layout.addWidget(admin_button)
        layout.addWidget(test_button)

        layout.addSpacing(30)

        # Информация
        info = QLabel("НИУ «МЭИ» • Кафедра физики им. В.А. Фабриканта • 2025")
        info.setStyleSheet("font-size: 11px; color: #95a5a6;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        # Установка фиксированных размеров
        admin_button.setMinimumHeight(70)
        test_button.setMinimumHeight(70)

        # Центрирование окна
        self.center_window()

    def create_mode_button(self, text: str, description: str,
                           color: str, callback) -> QPushButton:
        """Создание кнопки режима"""
        button = QPushButton(text)
        button.setStyleSheet(f"""
            QPushButton {{
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                background-color: {color};
                color: white;
                border-radius: 8px;
                text-align: left;
                padding-left: 20px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
        """)

        # Добавляем описание
        button.setToolTip(description)

        # Обработчик клика
        button.clicked.connect(callback)

        return button

    def darken_color(self, color: str) -> str:
        """Затемнение цвета для эффекта hover"""
        # Простая реализация затемнения
        colors = {
            "#3498db": "#2980b9",  # Синий
            "#2ecc71": "#27ae60",  # Зелёный
        }
        return colors.get(color, color)

    def center_window(self):
        """Центрирование окна на экране"""
        frame_geometry = self.frameGeometry()
        center_point = self.screen().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def open_admin_mode(self):
        """Открытие режима администратора"""
        dialog = LoginDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            username = dialog.username_input.text()
            try:
                self.admin_window = AdminWindow(username)
                self.admin_window.show()
                self.hide()
                self.admin_window.destroyed.connect(self.show)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно администратора:\n{e}")

    def open_test_mode(self):
        """Открытие режима тестирования"""
        self.test_window = TestLoginWindow(self)
        if self.test_window.exec() == QDialog.DialogCode.Accepted:
            self.hide()
            # Окно тестирования уже открыто через TestLoginWindow

def check_directories():
    """Проверка и создание необходимых директорий"""
    directories = [
        config.data_dir,
        config.tests_dir,
        config.results_dir,
        config.images_dir
    ]

    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Создана директория: {directory}")

def setup_application_style(app: QApplication):
    """Настройка стиля приложения"""
    # Светлая тема (по умолчанию)
    light_theme = """
        QMainWindow {
            background-color: #f5f5f5;
        }
        QLabel {
            color: #333333;
        }
        QPushButton {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #dddddd;
            padding: 10px;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #f0f0f0;
        }
        """
    app.setStyleSheet(light_theme)

if __name__ == "__main__":

    # Создаём приложение
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Устанавливаем иконку приложения
    app.setWindowIcon(QIcon())

    # Загружаем стиль
    setup_application_style(app)

    # Проверяем и создаём структуру папок
    check_directories()

    # Создаём и показываем главное окно
    window = MainWindow()
    window.show()

    # Запускаем приложение
    sys.exit(app.exec())