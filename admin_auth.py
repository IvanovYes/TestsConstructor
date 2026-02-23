
# admin_auth.py - Аутентификация администратора

from config import config
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox


class AdminAuth: # Класс для аутентификации администратора

    @staticmethod
    def authenticate(username: str, password: str) -> bool: # Проверка логина и пароля администратора
        admin_user, admin_pass = config.get_admin_credentials()
        return username == admin_user and password == admin_pass

    @staticmethod
    def change_password(new_password: str) -> bool: # Смена пароля администратора
        if len(new_password) < 4:
            return False

        config.update_admin_password(new_password)
        return True


class LoginDialog(QDialog): # Диалог входа администратора

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self): # Настройка интерфейса
        self.setWindowTitle("Вход администратора")
        self.setFixedSize(350, 250)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel("Конструктор Учебных Тестов")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Поля ввода
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Имя пользователя")
        layout.addWidget(QLabel("Имя пользователя:"))
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.password_input)

        # Кнопки
        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.authenticate)
        self.login_button.setDefault(True)

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)

        from PyQt6.QtWidgets import QHBoxLayout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def authenticate(self): # Аутентификация
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        if AdminAuth.authenticate(username, password):
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", "Неверное имя пользователя или пароль!")
            self.password_input.clear()
            self.password_input.setFocus()

class ChangePasswordDialog(QDialog): # Диалог смены пароля

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self): # Настройка интерфейса
        self.setWindowTitle("Смена пароля")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Текущий пароль
        layout.addWidget(QLabel("Текущий пароль:"))
        self.current_password = QLineEdit()
        self.current_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.current_password)

        # Новый пароль
        layout.addWidget(QLabel("Новый пароль:"))
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.new_password)

        # Подтверждение
        layout.addWidget(QLabel("Подтвердите новый пароль:"))
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.confirm_password)

        layout.addSpacing(20)

        # Кнопки
        self.change_button = QPushButton("Сменить пароль")
        self.change_button.clicked.connect(self.change_password)

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)

        from PyQt6.QtWidgets import QHBoxLayout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.change_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def change_password(self): # Смена пароля
        current = self.current_password.text()
        new = self.new_password.text()
        confirm = self.confirm_password.text()

        # Валидация
        if not AdminAuth.authenticate("admin", current):
            QMessageBox.critical(self, "Ошибка", "Неверный текущий пароль!")
            return

        if new != confirm:
            QMessageBox.critical(self, "Ошибка", "Пароли не совпадают!")
            return

        if len(new) < 4:
            QMessageBox.critical(self, "Ошибка", "Пароль должен быть не менее 4 символов!")
            return

        if AdminAuth.change_password(new):
            QMessageBox.information(self, "Успех", "Пароль успешно изменён!")
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось изменить пароль!")