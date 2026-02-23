"""
test_mode.py - Режим тестирования для прохождения тестов
"""
import os
import random
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from config import config
from utils import *
from test_compiler import TestCompiler
from results_manager import ResultsManager


class TestWindow(QMainWindow):
    """Окно прохождения теста"""

    test_completed = pyqtSignal(dict)

    def __init__(self, test_config, user_login: str, user_password: str):
        super().__init__()
        self.test_config = test_config
        self.user_login = user_login
        self.user_password = user_password

        self.questions_to_show = []
        self.current_question_index = 0
        self.user_answers = {}
        self.start_time = None
        self.time_left = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        self.results_manager = ResultsManager()

        self.setup_ui()
        self.prepare_questions()
        self.start_test()

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.setWindowTitle(f"Тестирование - {self.test_config.name}")
        self.setGeometry(100, 100, 1000, 700)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Панель информации
        info_panel = self.create_info_panel()
        layout.addWidget(info_panel)

        # Область вопроса
        self.question_stack = QStackedWidget()
        layout.addWidget(self.question_stack, 1)

        # Панель навигации
        nav_panel = self.create_navigation_panel()
        layout.addWidget(nav_panel)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

    def create_info_panel(self) -> QFrame:
        """Создание панели информации"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        panel.setMaximumHeight(80)

        layout = QHBoxLayout(panel)

        # Информация о тесте
        self.test_info_label = QLabel()
        self.test_info_label.setText(
            f"<b>Тест:</b> {self.test_config.name}<br>"
            f"<b>Студент:</b> {self.user_login}"
        )
        layout.addWidget(self.test_info_label)

        layout.addStretch()

        # Таймер
        timer_widget = QWidget()
        timer_layout = QVBoxLayout(timer_widget)

        self.timer_label = QLabel("Время: --:--")
        self.timer_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        timer_layout.addWidget(QLabel("Осталось времени:"))
        timer_layout.addWidget(self.timer_label)

        layout.addWidget(timer_widget)

        return panel

    def create_navigation_panel(self) -> QFrame:
        """Создание панели навигации"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        panel.setMaximumHeight(60)

        layout = QHBoxLayout(panel)

        # Кнопка "Назад"
        self.prev_button = QPushButton("← Назад")
        self.prev_button.clicked.connect(self.previous_question)
        self.prev_button.setMinimumWidth(100)

        # Кнопка "Далее"
        self.next_button = QPushButton("Далее →")
        self.next_button.clicked.connect(self.next_question)
        self.next_button.setMinimumWidth(100)

        # Кнопка "Завершить"
        self.finish_button = QPushButton("✅ Завершить тест")
        self.finish_button.clicked.connect(self.finish_test)
        self.finish_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.finish_button.setMinimumWidth(150)

        layout.addWidget(self.prev_button)
        layout.addStretch()
        layout.addWidget(self.next_button)
        layout.addStretch()
        layout.addWidget(self.finish_button)

        return panel

    def prepare_questions(self):
        """Подготовка вопросов для показа"""
        self.questions_to_show = []

        if self.test_config.mix_questions:
            # Перемешивание вопросов между блоками
            all_questions = []
            for block in self.test_config.blocks:
                # Выбор случайных вопросов из блока
                questions_from_block = block.questions.copy()
                random.shuffle(questions_from_block)
                questions_to_take = min(block.random_count, len(questions_from_block))
                all_questions.extend(questions_from_block[:questions_to_take])

            random.shuffle(all_questions)
            self.questions_to_show = all_questions
        else:
            # Последовательный вывод по блокам
            for block in self.test_config.blocks:
                questions_from_block = block.questions.copy()
                random.shuffle(questions_from_block)
                questions_to_take = min(block.random_count, len(questions_from_block))
                self.questions_to_show.extend(questions_from_block[:questions_to_take])

        # Инициализация ответов пользователя
        for i in range(len(self.questions_to_show)):
            self.user_answers[i] = {
                'answer': None,
                'is_answered': False,
                'question': self.questions_to_show[i]
            }

        # Создание виджетов вопросов
        self.create_question_widgets()

    def create_question_widgets(self):
        """Создание виджетов для всех вопросов"""
        for i, question in enumerate(self.questions_to_show):
            widget = self.create_question_widget(question, i)
            self.question_stack.addWidget(widget)

        # Обновление прогресс-бара
        self.progress_bar.setMaximum(len(self.questions_to_show))

    def create_question_widget(self, question: TestQuestion, index: int) -> QWidget:
        """Создание виджета для одного вопроса"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок вопроса
        question_header = QLabel(f"Вопрос {index + 1} из {len(self.questions_to_show)}")
        question_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(question_header)

        # Текст вопроса
        question_text = QLabel(question.text)
        question_text.setWordWrap(True)
        question_text.setStyleSheet("font-size: 14px; margin: 10px 0;")
        layout.addWidget(question_text)

        # Изображение (если есть)
        if question.image_path and os.path.exists(question.image_path):
            pixmap = load_pixmap(question.image_path)
            if pixmap:
                image_label = QLabel()
                image_label.setPixmap(pixmap)
                image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(image_label)

        # Виджет для ответа
        answer_widget = self.create_answer_widget(question, index)
        layout.addWidget(answer_widget)

        layout.addStretch()

        return widget

    def create_answer_widget(self, question: TestQuestion, index: int) -> QWidget:
        """Создание виджета для ответа на вопрос"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        if question.question_type in ["single", "multiple"]:
            # Создаем группу для радио-кнопок или чекбоксов
            if question.question_type == "single":
                group = QButtonGroup(widget)
                group.setExclusive(True)

                for i, option in enumerate(question.options):
                    rb = QRadioButton(option)
                    rb.setStyleSheet("font-size: 13px; margin: 5px; padding: 5px;")
                    group.addButton(rb, i)
                    layout.addWidget(rb)

                    # Восстановление сохраненного ответа
                    if (index in self.user_answers and
                            self.user_answers[index]['answer'] == i):
                        rb.setChecked(True)

                # Сохраняем группу для доступа
                widget.button_group = group

            else:  # multiple
                checkboxes = []
                for i, option in enumerate(question.options):
                    cb = QCheckBox(option)
                    cb.setStyleSheet("font-size: 13px; margin: 5px; padding: 5px;")
                    layout.addWidget(cb)
                    checkboxes.append(cb)

                    # Восстановление сохраненного ответа
                    if (index in self.user_answers and
                            i in self.user_answers[index]['answer']):
                        cb.setChecked(True)

                # Сохраняем чекбоксы для доступа
                widget.checkboxes = checkboxes

        else:  # text
            text_edit = QTextEdit()
            text_edit.setMaximumHeight(150)
            text_edit.setPlaceholderText("Введите ваш ответ здесь...")
            layout.addWidget(text_edit)

            # Восстановление сохраненного ответа
            if (index in self.user_answers and
                    self.user_answers[index]['answer']):
                text_edit.setText(self.user_answers[index]['answer'])

            # Сохраняем текстовое поле для доступа
            widget.text_edit = text_edit

        return widget

    def start_test(self):
        """Начало тестирования"""
        self.start_time = datetime.now()
        self.time_left = self.test_config.time_limit * 60  # в секундах

        # Запуск таймера
        self.timer.start(1000)

        # Показ первого вопроса
        self.show_question(0)

        # Обновление информации
        self.test_info_label.setText(
            f"<b>Тест:</b> {self.test_config.name}<br>"
            f"<b>Студент:</b> {self.user_login}<br>"
            f"<b>Вопросов:</b> {len(self.questions_to_show)}"
        )

    def show_question(self, index: int):
        """Показать вопрос с указанным индексом"""
        if 0 <= index < len(self.questions_to_show):
            # Сохраняем ответ на текущий вопрос
            self.save_current_answer()

            self.current_question_index = index
            self.question_stack.setCurrentIndex(index)

            # Обновление состояния кнопок
            self.prev_button.setEnabled(index > 0)
            self.next_button.setEnabled(index < len(self.questions_to_show) - 1)

            # Обновление прогресс-бара
            self.progress_bar.setValue(index + 1)

    def save_current_answer(self):
        """Сохранение ответа на текущий вопрос"""
        current_widget = self.question_stack.currentWidget()
        if not current_widget:
            return

        question = self.questions_to_show[self.current_question_index]
        answer_widget = current_widget.findChild(QWidget)

        if not answer_widget:
            return

        user_answer = None

        if question.question_type == "single":
            # Поиск выбранной радио-кнопки
            if hasattr(answer_widget, 'button_group'):
                checked_button = answer_widget.button_group.checkedButton()
                if checked_button:
                    user_answer = answer_widget.button_group.id(checked_button)

        elif question.question_type == "multiple":
            # Поиск отмеченных чекбоксов
            if hasattr(answer_widget, 'checkboxes'):
                checked_indices = []
                for i, cb in enumerate(answer_widget.checkboxes):
                    if cb.isChecked():
                        checked_indices.append(i)
                user_answer = checked_indices

        else:  # text
            # Получение текста из текстового поля
            if hasattr(answer_widget, 'text_edit'):
                user_answer = answer_widget.text_edit.toPlainText().strip()

        # Сохранение ответа
        self.user_answers[self.current_question_index]['answer'] = user_answer
        self.user_answers[self.current_question_index]['is_answered'] = user_answer not in [None, '', []]

    def previous_question(self):
        """Переход к предыдущему вопросу"""
        if self.current_question_index > 0:
            self.show_question(self.current_question_index - 1)

    def next_question(self):
        """Переход к следующему вопросу"""
        if self.current_question_index < len(self.questions_to_show) - 1:
            self.show_question(self.current_question_index + 1)

    def update_timer(self):
        """Обновление таймера"""
        if self.time_left > 0:
            self.time_left -= 1

            # Форматирование времени
            minutes = self.time_left // 60
            seconds = self.time_left % 60
            time_str = f"{minutes:02d}:{seconds:02d}"
            self.timer_label.setText(time_str)

            # Предупреждение при малом времени
            if self.time_left == 60:  # 1 минута
                self.timer_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff9800;")
                QMessageBox.warning(self, "Внимание", "Осталась 1 минута!")
            elif self.time_left <= 30:
                self.timer_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #f44336;")

        else:
            # Время вышло
            self.timer.stop()
            self.finish_test(forced=True)

    def finish_test(self, forced=False):
        """Завершение теста"""
        if not forced:
            reply = QMessageBox.question(
                self, "Завершение теста",
                "Вы уверены, что хотите завершить тест?\n\n"
                "После завершения вы не сможете изменить ответы.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

        self.timer.stop()
        self.save_current_answer()

        # Подсчёт результатов
        results = self.calculate_results()

        # Сохранение результатов
        result_file = self.results_manager.save_result(
            self.test_config,
            self.user_login,
            self.user_answers,
            self.start_time,
            datetime.now()
        )

        # Обновление теста (помечаем логин как использованный)
        self.test_config.mark_login_used(self.user_login)

        # Сохраняем обновлённый тест
        if self.test_config.filename:
            test_path = config.tests_dir / self.test_config.filename
            if test_path.exists():
                # Если тест скомпилирован, нужно декомпилировать, обновить и перекомпилировать
                compiler = TestCompiler()
                if compiler.is_compiled(str(test_path)):
                    import tempfile
                    fd, temp_xml = tempfile.mkstemp(suffix='.xml')
                    os.close(fd)

                    if compiler.decompile_test(str(test_path), temp_xml):
                        # Загружаем, обновляем, сохраняем
                        updated_config = load_test_from_xml(temp_xml)
                        if updated_config:
                            # Находим и обновляем логин
                            for i, (login, password, used) in enumerate(updated_config.credentials):
                                if login == self.user_login:
                                    updated_config.credentials[i] = (login, password, True)
                                    break

                            # Сохраняем и перекомпилируем
                            save_test_to_xml(updated_config, temp_xml)
                            compiler.compile_test(temp_xml, str(test_path))

                    os.unlink(temp_xml)
                else:
                    # Просто сохраняем обновлённый XML
                    save_test_to_xml(self.test_config, str(test_path))

        # Показ результатов
        self.show_results(results)

        # Закрытие окна
        self.close()

    def calculate_results(self) -> dict:
        """Подсчёт результатов теста"""
        score, max_score, percentage = self.results_manager.calculate_score(
            self.test_config, self.user_answers
        )

        duration = (datetime.now() - self.start_time).total_seconds()
        answered = sum(1 for a in self.user_answers.values() if a['is_answered'])

        return {
            'test_name': self.test_config.name,
            'user_login': self.user_login,
            'score': score,
            'max_score': max_score,
            'percentage': percentage,
            'answered': answered,
            'total': len(self.questions_to_show),
            'duration': int(duration),
            'start_time': self.start_time,
            'end_time': datetime.now()
        }

    def show_results(self, results: dict):
        """Показать результаты теста"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Результаты тестирования")
        dialog.setFixedSize(500, 400)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel("🎉 Тест завершён!")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #4CAF50;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(20)

        # Результаты
        results_text = f"""
        <table width="100%" cellspacing="10">
        <tr><td><b>Тест:</b></td><td>{results['test_name']}</td></tr>
        <tr><td><b>Студент:</b></td><td>{results['user_login']}</td></tr>
        <tr><td><b>Начало:</b></td><td>{results['start_time'].strftime('%d.%m.%Y %H:%M')}</td></tr>
        <tr><td><b>Завершение:</b></td><td>{results['end_time'].strftime('%d.%m.%Y %H:%M')}</td></tr>
        <tr><td><b>Длительность:</b></td><td>{results['duration'] // 60} мин {results['duration'] % 60} сек</td></tr>
        <tr><td colspan="2"><hr></td></tr>
        <tr><td><b>Набрано баллов:</b></td><td style="font-size: 18px; font-weight: bold;">{results['score']} из {results['max_score']}</td></tr>
        <tr><td><b>Процент выполнения:</b></td><td style="font-size: 18px; font-weight: bold; color: #2196F3;">{results['percentage']:.1f}%</td></tr>
        <tr><td><b>Отвечено вопросов:</b></td><td>{results['answered']} из {results['total']}</td></tr>
        </table>
        """

        results_label = QLabel(results_text)
        results_label.setWordWrap(True)
        layout.addWidget(results_label)

        layout.addSpacing(20)

        # Кнопки
        button_box = QDialogButtonBox()
        ok_button = button_box.addButton("OK", QDialogButtonBox.ButtonRole.AcceptRole)
        ok_button.clicked.connect(dialog.accept)

        layout.addWidget(button_box)

        dialog.exec()

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if self.timer.isActive():
            reply = QMessageBox.question(
                self, "Выход из теста",
                "Тест ещё не завершён. Вы уверены, что хотите выйти?\n\n"
                "Все несохранённые ответы будут потеряны.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

        event.accept()


class TestLoginWindow(QDialog):
    """Окно входа для тестируемого"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.test_config = None
        self.setup_ui()
        self.load_tests()

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.setWindowTitle("Вход в систему тестирования")
        self.setFixedSize(500, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        # Заголовок
        title = QLabel("Конструктор Учебных Тестов")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Режим тестирования")
        subtitle.setStyleSheet("font-size: 16px; color: #7f8c8d;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Выбор теста
        test_group = QGroupBox("Выбор теста")
        test_layout = QVBoxLayout(test_group)

        self.test_combo = QComboBox()
        self.test_combo.currentIndexChanged.connect(self.on_test_selected)
        test_layout.addWidget(QLabel("Доступные тесты:"))
        test_layout.addWidget(self.test_combo)

        self.test_description = QLabel()
        self.test_description.setWordWrap(True)
        self.test_description.setStyleSheet("color: #666; font-style: italic;")
        test_layout.addWidget(self.test_description)

        layout.addWidget(test_group)

        # Поля ввода
        form_group = QGroupBox("Аутентификация")
        form_layout = QFormLayout(form_group)

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Введите логин")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        form_layout.addRow("Логин:", self.login_input)
        form_layout.addRow("Пароль:", self.password_input)

        layout.addWidget(form_group)

        # Кнопки
        button_layout = QHBoxLayout()

        self.start_button = QPushButton("🎯 Начать тестирование")
        self.start_button.clicked.connect(self.start_testing)
        self.start_button.setDefault(True)
        self.start_button.setEnabled(False)

        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        # Сообщение о статусе
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)

    def load_tests(self):
        """Загрузка списка доступных тестов"""
        self.test_combo.clear()

        tests = config.get_test_list()
        for test in tests:
            if test['is_compiled']:
                icon = "🔒"
                self.test_combo.addItem(f"{icon} {test['name']}", test['filename'])

    def on_test_selected(self, index):
        """Обработка выбора теста"""
        if index >= 0:
            test_filename = self.test_combo.itemData(index)
            test = next((t for t in config.get_test_list() if t['filename'] == test_filename), None)

            if test:
                self.test_description.setText(test.get('description', 'Описание отсутствует'))
                self.update_test_status(test_filename)

    def update_test_status(self, test_filename: str):
        """Обновление статуса теста"""
        # Загружаем тест для проверки
        test_path = config.tests_dir / test_filename

        try:
            compiler = TestCompiler()
            if compiler.is_compiled(str(test_path)):
                # Для скомпилированных тестов нужна декомпиляция
                import tempfile
                fd, temp_xml = tempfile.mkstemp(suffix='.xml')
                os.close(fd)

                if compiler.decompile_test(str(test_path), temp_xml):
                    self.test_config = load_test_from_xml(temp_xml)
                    os.unlink(temp_xml)
                else:
                    self.test_config = None
            else:
                self.test_config = load_test_from_xml(str(test_path))

            if self.test_config:
                unused = len(self.test_config.get_unused_logins())
                total = len(self.test_config.credentials)

                if total > 0:
                    self.status_label.setText(f"Доступно {unused} из {total} логинов")
                    self.start_button.setEnabled(True)
                else:
                    self.status_label.setText("Для этого теста не настроены логины")
                    self.start_button.setEnabled(False)
            else:
                self.status_label.setText("Не удалось загрузить тест")
                self.start_button.setEnabled(False)

        except Exception as e:
            self.status_label.setText(f"Ошибка загрузки теста: {str(e)}")
            self.start_button.setEnabled(False)

    def start_testing(self):
        """Начало тестирования"""
        if not self.test_config:
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить тест!")
            return

        login = self.login_input.text().strip()
        password = self.password_input.text().strip()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль!")
            return

        # Проверка логина и пароля
        valid = False
        for stored_login, stored_password, used in self.test_config.credentials:
            if stored_login == login and stored_password == password:
                if not used:
                    valid = True
                    break
                else:
                    QMessageBox.critical(self, "Ошибка", "Этот логин уже был использован!")
                    return

        if not valid:
            QMessageBox.critical(self, "Ошибка", "Неверный логин или пароль!")
            return

        # Закрытие диалога и открытие окна тестирования
        self.accept()

        self.test_window = TestWindow(self.test_config, login, password)
        self.test_window.show()