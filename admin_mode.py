
# admin_mode.py - Режим администратора для создания и редактирования тестов

import os
import shutil
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from config import config
from utils import *
from test_compiler import TestCompiler, compile_selected_test
from results_manager import ResultsManager


class AdminWindow(QMainWindow): # Главное окно администратора

    def __init__(self, username: str):
        super().__init__()
        self.username = username
        self.current_test = TestConfig()
        self.current_block = None
        self.current_question = None
        self.results_manager = ResultsManager()

        self.setup_ui()
        self.load_tests_list()

    def setup_ui(self): # Настройка пользовательского интерфейса
        self.setWindowTitle(f"КУТ - Администратор ({self.username})")
        self.setGeometry(100, 100, 1400, 800)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Левая панель - меню и список тестов
        left_panel = self.create_left_panel()

        # Правая панель - редактор теста
        right_panel = self.create_right_panel()

        # Разделитель
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 1100])

        main_layout.addWidget(splitter)

        # Статус бар
        self.statusBar().showMessage(f"Добро пожаловать, {self.username}! | Тестов: {len(config.get_test_list())}")

        # Меню
        #self.setup_menu()

    def create_left_panel(self) -> QWidget: # Создание левой панели
        panel = QWidget()
        panel.setMinimumWidth(250)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # Панель управления
        control_group = QGroupBox("Управление тестами")
        control_layout = QVBoxLayout(control_group)

        # Кнопки
        buttons = [
            ("📝 Новый тест", self.new_test, "Создать новый тест"),
            ("📂 Загрузить тест", self.load_test, "Загрузить тест из файла"),
            ("💾 Сохранить тест", self.save_test, "Сохранить текущий тест"),
            ("🔒 Скомпилировать", self.compile_test, "Скомпилировать тест"),
            #("📊 Просмотр результатов", self.view_results, "Просмотреть результаты"),
            ("⚙️ Настройки", self.open_settings, "Настройки программы")
        ]

        for text, slot, tooltip in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            btn.setToolTip(tooltip)
            control_layout.addWidget(btn)

        layout.addWidget(control_group)

        # Список тестов
        list_group = QGroupBox("Доступные тесты")
        list_layout = QVBoxLayout(list_group)

        self.tests_list = QListWidget()
        self.tests_list.itemDoubleClicked.connect(self.load_selected_test)
        self.tests_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tests_list.customContextMenuRequested.connect(self.show_test_context_menu)

        list_layout.addWidget(self.tests_list)

        layout.addWidget(list_group)
        layout.addStretch()

        return panel

    def create_right_panel(self) -> QTabWidget: # Создание правой панели с вкладками
        tab_widget = QTabWidget()

        # Вкладка "Информация о тесте"
        tab_widget.addTab(self.create_info_tab(), "📋 Информация")

        # Вкладка "Блоки вопросов"
        tab_widget.addTab(self.create_blocks_tab(), "📚 Блоки вопросов")

        # Вкладка "Редактор вопроса"
        tab_widget.addTab(self.create_question_tab(), "❓ Редактор вопроса")

        # Вкладка "Пользователи"
        tab_widget.addTab(self.create_users_tab(), "👥 Пользователи")

        # Вкладка "Результаты"
        tab_widget.addTab(self.create_results_tab(), "📊 Результаты")

        return tab_widget

    def create_info_tab(self) -> QWidget: # Создание вкладки с информацией о тесте
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Название теста
        self.test_name = QLineEdit()
        self.test_name.setPlaceholderText("Введите название теста")
        layout.addRow("Название теста:", self.test_name)

        # Описание
        self.test_description = QTextEdit()
        self.test_description.setMaximumHeight(100)
        self.test_description.setPlaceholderText("Введите описание теста")
        layout.addRow("Описание:", self.test_description)

        # Максимальный балл
        self.test_max_score = QSpinBox()
        self.test_max_score.setRange(1, 1000)
        self.test_max_score.setValue(100)
        layout.addRow("Максимальный балл:", self.test_max_score)

        # Ограничение времени
        self.test_time_limit = QSpinBox()
        self.test_time_limit.setRange(1, 300)
        self.test_time_limit.setValue(60)
        self.test_time_limit.setSuffix(" минут")
        layout.addRow("Ограничение времени:", self.test_time_limit)

        # Перемешивание вопросов
        self.test_mix_questions = QCheckBox("Перемешивать вопросы между блоками")
        layout.addRow("", self.test_mix_questions)

        # Статистика
        stats_group = QGroupBox("Статистика теста")
        stats_layout = QFormLayout(stats_group)

        self.stats_usage = QLabel("0")
        self.stats_last_used = QLabel("Никогда")
        self.stats_credentials = QLabel("0 / 0")

        stats_layout.addRow("Использований:", self.stats_usage)
        stats_layout.addRow("Последнее использование:", self.stats_last_used)
        stats_layout.addRow("Логины (использовано/всего):", self.stats_credentials)

        layout.addRow(stats_group)

        layout.addRow(QLabel(""))  # Отступ

        # Кнопка сохранения
        save_btn = QPushButton("💾 Сохранить информацию")
        save_btn.clicked.connect(self.save_test_info)
        layout.addRow(save_btn)

        return widget

    def create_blocks_tab(self) -> QWidget: # Создание вкладки с блоками вопросов
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Панель управления блоками
        block_control = QHBoxLayout()

        btn_add_block = QPushButton("➕ Добавить блок")
        btn_add_block.clicked.connect(self.add_block)

        btn_remove_block = QPushButton("➖ Удалить блок")
        btn_remove_block.clicked.connect(self.remove_block)

        btn_up_block = QPushButton("⬆️ Вверх")
        btn_up_block.clicked.connect(self.move_block_up)

        btn_down_block = QPushButton("⬇️ Вниз")
        btn_down_block.clicked.connect(self.move_block_down)

        block_control.addWidget(btn_add_block)
        block_control.addWidget(btn_remove_block)
        block_control.addWidget(btn_up_block)
        block_control.addWidget(btn_down_block)
        block_control.addStretch()

        layout.addLayout(block_control)

        # Список блоков
        self.blocks_list = QListWidget()
        self.blocks_list.itemClicked.connect(self.select_block)
        layout.addWidget(self.blocks_list)

        # Параметры блока
        block_params = QGroupBox("Параметры блока")
        params_layout = QFormLayout(block_params)

        self.block_name = QLineEdit()
        self.block_name.textChanged.connect(self.update_block_name)

        self.block_random_count = QSpinBox()
        self.block_random_count.setRange(1, 15)
        self.block_random_count.setValue(1)
        self.block_random_count.valueChanged.connect(self.update_block_random_count)

        params_layout.addRow("Название блока:", self.block_name)
        params_layout.addRow("Случайных вопросов:", self.block_random_count)

        layout.addWidget(block_params)

        return widget

    def create_question_tab(self) -> QWidget: # Создание вкладки редактирования вопроса
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Панель управления вопросами
        question_control = QHBoxLayout()

        btn_add_question = QPushButton("➕ Добавить вопрос")
        btn_add_question.clicked.connect(self.add_question)

        btn_remove_question = QPushButton("➖ Удалить вопрос")
        btn_remove_question.clicked.connect(self.remove_question)

        btn_copy_question = QPushButton("📋 Копировать вопрос")
        btn_copy_question.clicked.connect(self.copy_question)

        # Кнопка сохранения
        btn_save_question = QPushButton("💾 Сохранить вопрос")
        btn_save_question.clicked.connect(self.save_question)

        question_control.addWidget(btn_add_question)
        question_control.addWidget(btn_remove_question)
        question_control.addWidget(btn_copy_question)
        question_control.addWidget(btn_save_question)
        question_control.addStretch()
        layout.addLayout(question_control)

        # Список вопросов
        self.questions_list = QListWidget()
        self.questions_list.itemClicked.connect(self.select_question)
        layout.addWidget(self.questions_list)

        # Редактор вопроса
        editor = QGroupBox("Редактор вопроса")
        editor_layout = QVBoxLayout(editor)

        # Тип вопроса
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Тип вопроса:"))

        self.question_type_single = QRadioButton("Один ответ")
        self.question_type_single.toggled.connect(self.on_question_type_changed)
        self.question_type_multiple = QRadioButton("Несколько ответов")
        self.question_type_multiple.toggled.connect(self.on_question_type_changed)
        self.question_type_text = QRadioButton("Текстовый ответ")
        self.question_type_text.toggled.connect(self.on_question_type_changed)

        type_layout.addWidget(self.question_type_single)
        type_layout.addWidget(self.question_type_multiple)
        type_layout.addWidget(self.question_type_text)
        type_layout.addStretch()

        editor_layout.addLayout(type_layout)

        # Текст вопроса
        editor_layout.addWidget(QLabel("Текст вопроса:"))
        self.question_text = QTextEdit()
        self.question_text.setMaximumHeight(100)
        editor_layout.addWidget(self.question_text)

        # Изображение
        image_layout = QHBoxLayout()

        self.question_image_path = QLineEdit()
        self.question_image_path.setReadOnly(True)

        btn_browse_image = QPushButton("📁 Выбрать...")
        btn_browse_image.clicked.connect(self.browse_question_image)

        btn_clear_image = QPushButton("❌ Очистить")
        btn_clear_image.clicked.connect(self.clear_question_image)

        image_layout.addWidget(QLabel("Изображение:"))
        image_layout.addWidget(self.question_image_path)
        image_layout.addWidget(btn_browse_image)
        image_layout.addWidget(btn_clear_image)

        editor_layout.addLayout(image_layout)

        # Баллы
        points_layout = QHBoxLayout()
        points_layout.addWidget(QLabel("Баллы за вопрос:"))

        self.question_points = QSpinBox()
        self.question_points.setRange(1, 100)
        self.question_points.setValue(1)

        points_layout.addWidget(self.question_points)
        points_layout.addStretch()

        editor_layout.addLayout(points_layout)

        # Варианты ответов (для single/multiple)
        self.answers_frame = self.create_answers_frame()
        editor_layout.addWidget(self.answers_frame)

        # Правильный ответ (для текстовых)
        self.text_answer_frame = self.create_text_answer_frame()
        editor_layout.addWidget(self.text_answer_frame)
        layout.addWidget(editor)
        return widget

    def create_answers_frame(self) -> QGroupBox: # Создание фрейма для вариантов ответов
        frame = QGroupBox("Варианты ответов")
        layout = QVBoxLayout(frame)

        # Управление вариантами
        control_layout = QHBoxLayout()

        btn_add_option = QPushButton("➕ Добавить")
        btn_add_option.clicked.connect(self.add_option)

        btn_remove_option = QPushButton("➖ Удалить")
        btn_remove_option.clicked.connect(self.remove_option)

        btn_up_option = QPushButton("⬆️ Вверх")
        btn_up_option.clicked.connect(self.move_option_up)

        btn_down_option = QPushButton("⬇️ Вниз")
        btn_down_option.clicked.connect(self.move_option_down)

        control_layout.addWidget(btn_add_option)
        control_layout.addWidget(btn_remove_option)
        control_layout.addWidget(btn_up_option)
        control_layout.addWidget(btn_down_option)
        control_layout.addStretch()

        layout.addLayout(control_layout)

        # Список вариантов
        self.options_list = QListWidget()
        #self.options_list.setMaximumHeight(150)
        #layout.addWidget(self.options_list)

        # Поле для нового варианта
        self.new_option_text = QLineEdit()
        self.new_option_text.setPlaceholderText("Введите вариант ответа...")
        self.new_option_text.returnPressed.connect(self.add_option)
        layout.addWidget(self.new_option_text)

        # Правильные ответы
        self.correct_answers_label = QLabel("Правильные ответы (отметьте галочками):")
        layout.addWidget(self.correct_answers_label)

        # Контейнер для чекбоксов
        self.correct_answers_widget = QWidget()
        self.correct_answers_layout = QVBoxLayout(self.correct_answers_widget)
        layout.addWidget(self.correct_answers_widget)

        return frame

    def create_text_answer_frame(self) -> QGroupBox: # Создание фрейма для текстового ответа
        frame = QGroupBox("Правильный текстовый ответ")
        layout = QVBoxLayout(frame)

        self.correct_text_answer = QLineEdit()
        self.correct_text_answer.setPlaceholderText("Введите правильный ответ...")
        layout.addWidget(self.correct_text_answer)

        frame.setVisible(False)
        return frame

    def create_users_tab(self) -> QWidget: # Создание вкладки управления пользователями
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Панель генерации
        generate_group = QGroupBox("Генерация логинов/паролей")
        generate_layout = QFormLayout(generate_group)

        self.users_count = QSpinBox()
        self.users_count.setRange(1, 1000)
        self.users_count.setValue(10)

        self.users_prefix = QLineEdit()
        self.users_prefix.setText("student")

        btn_generate = QPushButton("🎲 Сгенерировать")
        btn_generate.clicked.connect(self.generate_users)

        generate_layout.addRow("Количество:", self.users_count)
        generate_layout.addRow("Префикс логинов:", self.users_prefix)
        generate_layout.addRow(btn_generate)

        layout.addWidget(generate_group)

        # Таблица пользователей
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(3)
        self.users_table.setHorizontalHeaderLabels(["Логин", "Пароль", "Использован"])
        self.users_table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.users_table)

        # Панель управления
        user_control = QHBoxLayout()

        btn_export = QPushButton("📤 Экспорт в CSV")
        btn_export.clicked.connect(self.export_users)

        btn_import = QPushButton("📥 Импорт из CSV")
        btn_import.clicked.connect(self.import_users)

        btn_clear = QPushButton("🗑️ Очистить все")
        btn_clear.clicked.connect(self.clear_users)

        user_control.addWidget(btn_export)
        user_control.addWidget(btn_import)
        user_control.addWidget(btn_clear)
        user_control.addStretch()

        layout.addLayout(user_control)

        return widget

    def create_results_tab(self) -> QWidget: # Создание вкладки просмотра результатов
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Выбор теста для просмотра
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Тест:"))

        self.results_test_combo = QComboBox()
        self.update_results_test_combo()

        btn_refresh = QPushButton("🔄 Обновить")
        btn_refresh.clicked.connect(self.refresh_results)

        btn_export_results = QPushButton("📊 Экспорт результатов")
        btn_export_results.clicked.connect(self.export_all_results)

        select_layout.addWidget(self.results_test_combo)
        select_layout.addWidget(btn_refresh)
        select_layout.addWidget(btn_export_results)
        select_layout.addStretch()

        layout.addLayout(select_layout)

        # Таблица результатов
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            "Логин", "Дата", "Баллы", "Макс.", "%",
            "Время", "Длит. (сек)", "Файл"
        ])

        layout.addWidget(self.results_table)

        # Статистика
        stats_group = QGroupBox("Статистика")
        stats_layout = QGridLayout(stats_group)

        self.stats_total = QLabel("0")
        self.stats_avg_score = QLabel("0")
        self.stats_avg_percent = QLabel("0%")
        self.stats_best = QLabel("0")
        self.stats_worst = QLabel("0")

        stats_layout.addWidget(QLabel("Всего попыток:"), 0, 0)
        stats_layout.addWidget(self.stats_total, 0, 1)
        stats_layout.addWidget(QLabel("Средний балл:"), 0, 2)
        stats_layout.addWidget(self.stats_avg_score, 0, 3)
        stats_layout.addWidget(QLabel("Средний %:"), 1, 0)
        stats_layout.addWidget(self.stats_avg_percent, 1, 1)
        stats_layout.addWidget(QLabel("Лучший результат:"), 1, 2)
        stats_layout.addWidget(self.stats_best, 1, 3)
        stats_layout.addWidget(QLabel("Худший результат:"), 2, 0)
        stats_layout.addWidget(self.stats_worst, 2, 1)

        layout.addWidget(stats_group)

        return widget

    def setup_menu(self): # Настройка меню
        menubar = self.menuBar()

        # Меню Файл
        file_menu = menubar.addMenu("📁 Файл")

        new_action = QAction("📝 Новый тест", self)
        new_action.triggered.connect(self.new_test)
        file_menu.addAction(new_action)

        load_action = QAction("📂 Загрузить тест...", self)
        load_action.triggered.connect(self.load_test)
        file_menu.addAction(load_action)

        save_action = QAction("💾 Сохранить тест...", self)
        save_action.triggered.connect(self.save_test)
        file_menu.addAction(save_action)

        compile_action = QAction("🔒 Скомпилировать тест...", self)
        compile_action.triggered.connect(self.compile_test)
        file_menu.addAction(compile_action)

        file_menu.addSeparator()

        exit_action = QAction("🚪 Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню Редактирование
        edit_menu = menubar.addMenu("✏️ Редактирование")

        add_block_action = QAction("📚 Добавить блок", self)
        add_block_action.triggered.connect(self.add_block)
        edit_menu.addAction(add_block_action)

        add_question_action = QAction("❓ Добавить вопрос", self)
        add_question_action.triggered.connect(self.add_question)
        edit_menu.addAction(add_question_action)

        # Меню Сервис
        tools_menu = menubar.addMenu("🛠️ Сервис")

        results_action = QAction("📊 Просмотр результатов", self)
        results_action.triggered.connect(self.view_results)
        tools_menu.addAction(results_action)

        settings_action = QAction("⚙️ Настройки", self)
        settings_action.triggered.connect(self.open_settings)
        tools_menu.addAction(settings_action)

        # Меню Помощь
        help_menu = menubar.addMenu("❓ Помощь")

        about_action = QAction("ℹ️ О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    # === МЕТОДЫ ДЛЯ РАБОТЫ С ТЕСТАМИ ===

    def new_test(self): # Создание нового теста
        if self.current_test and self.current_test.name:
            reply = QMessageBox.question(
                self, "Новый тест",
                "Сохранить текущий тест перед созданием нового?",
                QMessageBox.StandardButton.Yes |
                QMessageBox.StandardButton.No |
                QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Yes:
                if not self.save_test():
                    return

        self.current_test = TestConfig()
        self.current_block = None
        self.current_question = None

        self.update_test_info_display()
        self.blocks_list.clear()
        self.questions_list.clear()
        self.users_table.setRowCount(0)

        self.statusBar().showMessage("Создан новый тест")
        show_message(self, "Новый тест", "Создан новый тест. Заполните информацию.")

    def load_test(self): # Загрузка теста из файла
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Загрузить тест",
            str(config.tests_dir),
            "Тесты (*.xml *.kut);;Все файлы (*.*)"
        )

        if file_path:
            self.load_test_from_path(file_path)

    def load_test_from_path(self, file_path: str): # Загрузка теста по указанному пути
        try:
            # Проверяем, скомпилирован ли тест
            compiler = TestCompiler()
            if compiler.is_compiled(file_path):
                # Декомпилируем во временный файл
                import tempfile
                fd, temp_path = tempfile.mkstemp(suffix='.xml')
                os.close(fd)

                if compiler.decompile_test(file_path, temp_path):
                    test_config = load_test_from_xml(temp_path)
                    os.unlink(temp_path)
                else:
                    show_message(self, "Ошибка", "Не удалось декомпилировать тест!")
                    return
            else:
                test_config = load_test_from_xml(file_path)

            if test_config:
                self.current_test = test_config
                self.current_test.filename = os.path.basename(file_path)

                self.update_test_info_display()
                self.update_blocks_list()
                self.update_users_table()

                self.statusBar().showMessage(f"Загружен тест: {test_config.name}")
                show_message(self, "Успех", f"Тест '{test_config.name}' загружен.")
            else:
                show_message(self, "Ошибка", "Не удалось загрузить тест!")

        except Exception as e:
            show_message(self, "Ошибка", f"Ошибка загрузки теста: {str(e)}")

    def save_test(self) -> bool: # Сохранение теста в файл
        if not self.current_test.name:
            show_message(self, "Ошибка", "Введите название теста!", QMessageBox.Icon.Warning)
            return False

        # Сохраняем данные из UI
        self.save_test_info_from_ui()

        # Определяем имя файла
        if not self.current_test.filename:
            safe_name = self.current_test.name.replace(" ", "_").replace("/", "_")
            self.current_test.filename = f"{safe_name}.xml"

        file_path = config.tests_dir / self.current_test.filename

        # Сохраняем
        if save_test_to_xml(self.current_test, str(file_path)):
            show_message(self, "Успех", f"Тест сохранен: {file_path.name}")
            self.load_tests_list()
            return True
        else:
            show_message(self, "Ошибка", "Не удалось сохранить тест!")
            return False

    def compile_test(self): # Компиляция теста
        if not self.current_test.blocks:
            show_message(self, "Ошибка", "Добавьте хотя бы один блок вопросов!", QMessageBox.Icon.Warning)
            return

        # Сначала сохраняем тест
        if not self.save_test():
            return

        file_path = config.tests_dir / self.current_test.filename

        # Компилируем
        if compile_selected_test(str(file_path)):
            # Удаляем исходный XML (опционально)
            reply = QMessageBox.question(
                self, "Компиляция",
                "Тест успешно скомпилирован! Удалить исходный XML файл?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                os.remove(file_path)

            show_message(self, "Успех", "Тест скомпилирован и сохранен в формате .kut")
            self.load_tests_list()
        else:
            show_message(self, "Ошибка", "Не удалось скомпилировать тест!")

    def save_test_info_from_ui(self): # Сохранение информации о тесте из UI
        self.current_test.name = self.test_name.text()
        self.current_test.description = self.test_description.toPlainText()
        self.current_test.max_score = self.test_max_score.value()
        self.current_test.time_limit = self.test_time_limit.value()
        self.current_test.mix_questions = self.test_mix_questions.isChecked()

    def update_test_info_display(self): # Обновление отображения информации о тесте
        self.test_name.setText(self.current_test.name)
        self.test_description.setText(self.current_test.description)
        self.test_max_score.setValue(self.current_test.max_score)
        self.test_time_limit.setValue(self.current_test.time_limit)
        self.test_mix_questions.setChecked(self.current_test.mix_questions)

        # Статистика
        self.stats_usage.setText(str(self.current_test.usage_count))

        if self.current_test.last_used:
            self.stats_last_used.setText(self.current_test.last_used.strftime("%d.%m.%Y %H:%M"))
        else:
            self.stats_last_used.setText("Никогда")

        used = sum(1 for _, _, u in self.current_test.credentials if u)
        total = len(self.current_test.credentials)
        self.stats_credentials.setText(f"{used} / {total}")

    # === МЕТОДЫ ДЛЯ РАБОТЫ С БЛОКАМИ ===

    def add_block(self): # Добавление нового блока вопросов
        block = TestBlock()
        block.id = len(self.current_test.blocks) + 1
        block.name = f"Блок {block.id}"
        self.current_test.blocks.append(block)

        self.update_blocks_list()
        self.blocks_list.setCurrentRow(len(self.current_test.blocks) - 1)
        self.select_block()

    def remove_block(self): # Удаление блока вопросов
        if not self.current_block:
            return

        row = self.blocks_list.currentRow()
        if row >= 0:
            reply = QMessageBox.question(
                self, "Удаление блока",
                f"Удалить блок '{self.current_block.name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.current_test.blocks.pop(row)
                self.update_blocks_list()
                self.current_block = None
                self.questions_list.clear()

    def move_block_up(self): # Перемещение блока вверх
        row = self.blocks_list.currentRow()
        if row > 0:
            self.current_test.blocks[row], self.current_test.blocks[row - 1] = \
                self.current_test.blocks[row - 1], self.current_test.blocks[row]
            self.update_blocks_list()
            self.blocks_list.setCurrentRow(row - 1)

    def move_block_down(self): # Перемещение блока вниз
        row = self.blocks_list.currentRow()
        if row < len(self.current_test.blocks) - 1:
            self.current_test.blocks[row], self.current_test.blocks[row + 1] = \
                self.current_test.blocks[row + 1], self.current_test.blocks[row]
            self.update_blocks_list()
            self.blocks_list.setCurrentRow(row + 1)

    def select_block(self): # Выбор блока для редактирования
        row = self.blocks_list.currentRow()
        if 0 <= row < len(self.current_test.blocks):
            self.current_block = self.current_test.blocks[row]
            self.update_block_info_display()
            self.update_questions_list()

    def update_blocks_list(self): # Обновление списка блоков
        self.blocks_list.clear()
        for block in self.current_test.blocks:
            item = QListWidgetItem(f"{block.id}. {block.name} ({len(block.questions)} вопросов)")
            self.blocks_list.addItem(item)

    def update_block_info_display(self): # Обновление отображения информации о блоке
        if self.current_block:
            self.block_name.setText(self.current_block.name)
            self.block_random_count.setValue(self.current_block.random_count)

    def update_block_name(self): # Обновление имени блока
        if self.current_block:
            self.current_block.name = self.block_name.text()
            self.update_blocks_list()

    def update_block_random_count(self): # Обновление количества случайных вопросов
        if self.current_block:
            self.current_block.random_count = self.block_random_count.value()

    # === МЕТОДЫ ДЛЯ РАБОТЫ С ВОПРОСАМИ ===

    def add_question(self): # Добавление нового вопроса
        if not self.current_block:
            show_message(self, "Ошибка", "Сначала выберите или создайте блок!", QMessageBox.Icon.Warning)
            return

        question = TestQuestion()
        question.id = len(self.current_block.questions) + 1
        question.text = f"Вопрос {question.id}"
        question.block_id = self.current_block.id
        self.current_block.questions.append(question)

        self.update_questions_list()
        self.questions_list.setCurrentRow(len(self.current_block.questions) - 1)
        self.select_question()
        self.update_blocks_list()

    def remove_question(self): # Удаление вопроса
        if not self.current_block or not self.current_question:
            return

        row = self.questions_list.currentRow()
        if row >= 0:
            reply = QMessageBox.question(
                self, "Удаление вопроса",
                "Удалить выбранный вопрос?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.current_block.questions.pop(row)
                self.update_questions_list()
                self.current_question = None

    def copy_question(self): # Копирование вопроса
        if not self.current_question:
            return

        import copy
        new_question = copy.deepcopy(self.current_question)
        new_question.id = len(self.current_block.questions) + 1
        new_question.text = f"{new_question.text} (копия)"

        self.current_block.questions.append(new_question)
        self.update_questions_list()

    def select_question(self): # Выбор вопроса для редактирования
        row = self.questions_list.currentRow()
        if 0 <= row < len(self.current_block.questions):
            self.current_question = self.current_block.questions[row]
            self.update_question_display()

    def update_questions_list(self): # Обновление списка вопросов
        self.questions_list.clear()
        if self.current_block:
            for question in self.current_block.questions:
                text_preview = question.text[:50] + "..." if len(question.text) > 50 else question.text
                item = QListWidgetItem(f"{question.id}. {text_preview}")
                self.questions_list.addItem(item)

    def update_question_display(self): # Обновление отображения вопроса
        if not self.current_question:
            return

        # Тип вопроса
        if self.current_question.question_type == "single":
            self.question_type_single.setChecked(True)
        elif self.current_question.question_type == "multiple":
            self.question_type_multiple.setChecked(True)
        else:  # text
            self.question_type_text.setChecked(True)

        self.on_question_type_changed()

        # Текст вопроса
        self.question_text.setPlainText(self.current_question.text)

        # Изображение
        self.question_image_path.setText(self.current_question.image_path)

        # Баллы
        self.question_points.setValue(self.current_question.points)

        # Варианты ответов
        self.update_options_list()

        # Правильные ответы
        self.update_correct_answers_display()

        # Текстовый ответ
        if (self.current_question.question_type == "text" and
                self.current_question.correct_answers):
            self.correct_text_answer.setText(str(self.current_question.correct_answers[0]))

    def on_question_type_changed(self): # Обработка изменения типа вопроса
        if self.question_type_single.isChecked() or self.question_type_multiple.isChecked():
            self.answers_frame.setVisible(True)
            self.text_answer_frame.setVisible(False)
        else:
            self.answers_frame.setVisible(False)
            self.text_answer_frame.setVisible(True)

    def update_options_list(self): # Обновление списка вариантов ответов
        self.options_list.clear()
        if self.current_question:
            for i, option in enumerate(self.current_question.options):
                self.options_list.addItem(f"{i + 1}. {option}")

    def update_correct_answers_display(self): # Обновление отображения правильных ответов
        # Очищаем старые чекбоксы
        for i in reversed(range(self.correct_answers_layout.count())):
            widget = self.correct_answers_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Создаем новые чекбоксы
        if self.current_question and self.current_question.options:
            for i, option in enumerate(self.current_question.options):
                checkbox = QCheckBox(f"{i + 1}. {option}")
                checkbox.setChecked(i in self.current_question.correct_answers)
                checkbox.stateChanged.connect(self.update_correct_answers_from_ui)
                self.correct_answers_layout.addWidget(checkbox)

    def update_correct_answers_from_ui(self): # Обновление правильных ответов из UI
        if not self.current_question:
            return

        self.current_question.correct_answers = []
        for i in range(self.correct_answers_layout.count()):
            widget = self.correct_answers_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox) and widget.isChecked():
                self.current_question.correct_answers.append(i)

    def save_question(self): # Сохранение вопроса
        if not self.current_question:
            return

        # Сохранение типа
        if self.question_type_single.isChecked():
            self.current_question.question_type = "single"
        elif self.question_type_multiple.isChecked():
            self.current_question.question_type = "multiple"
        else:
            self.current_question.question_type = "text"
            # Для текстовых вопросов
            text_answer = self.correct_text_answer.text().strip()
            if text_answer:
                self.current_question.correct_answers = [text_answer]

        # Сохранение текста
        self.current_question.text = self.question_text.toPlainText()

        # Сохранение баллов
        self.current_question.points = self.question_points.value()

        # Сохранение изображения
        self.current_question.image_path = self.question_image_path.text()

        # Обновление списка
        self.update_questions_list()

        show_message(self, "Сохранение", "Вопрос сохранен успешно!")

    # === МЕТОДЫ ДЛЯ ВАРИАНТОВ ОТВЕТОВ ===

    def add_option(self): # Добавление варианта ответа
        option_text = self.new_option_text.text().strip()
        if option_text and self.current_question:
            self.current_question.options.append(option_text)
            self.update_options_list()
            self.update_correct_answers_display()
            self.new_option_text.clear()

    def remove_option(self): # Удаление варианта ответа
        row = self.options_list.currentRow()
        if row >= 0 and self.current_question and row < len(self.current_question.options):
            self.current_question.options.pop(row)
            self.update_options_list()
            self.update_correct_answers_display()

    def move_option_up(self): # Перемещение варианта вверх
        row = self.options_list.currentRow()
        if row > 0 and self.current_question:
            self.current_question.options[row], self.current_question.options[row - 1] = \
                self.current_question.options[row - 1], self.current_question.options[row]
            self.update_options_list()
            self.options_list.setCurrentRow(row - 1)
            self.update_correct_answers_display()

    def move_option_down(self): # Перемещение варианта вниз
        row = self.options_list.currentRow()
        if row < len(self.current_question.options) - 1 and self.current_question:
            self.current_question.options[row], self.current_question.options[row + 1] = \
                self.current_question.options[row + 1], self.current_question.options[row]
            self.update_options_list()
            self.options_list.setCurrentRow(row + 1)
            self.update_correct_answers_display()

    def browse_question_image(self): # Выбор изображения для вопроса
        file_path = browse_image(self, self.question_image_path.text())
        if file_path:
            # Пытаемся скопировать изображение в папку проекта
            try:
                dest_path = config.images_dir / os.path.basename(file_path)
                shutil.copy2(file_path, dest_path)
                self.question_image_path.setText(str(dest_path))
            except:
                self.question_image_path.setText(file_path)

    def clear_question_image(self): # Очистка изображения вопроса
        self.question_image_path.clear()

    # === МЕТОДЫ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ===

    def generate_users(self): # Генерация логинов/паролей
        count = self.users_count.value()
        prefix = self.users_prefix.text().strip() or "student"

        self.current_test.add_credentials(count, prefix)
        self.update_users_table()

    def update_users_table(self): # Обновление таблицы пользователей
        self.users_table.setRowCount(len(self.current_test.credentials))

        for i, (login, password, used) in enumerate(self.current_test.credentials):
            self.users_table.setItem(i, 0, QTableWidgetItem(login))
            self.users_table.setItem(i, 1, QTableWidgetItem(password))
            self.users_table.setItem(i, 2, QTableWidgetItem("Да" if used else "Нет"))

    def export_users(self): # Экспорт пользователей в CSV
        if not self.current_test.credentials:
            show_message(self, "Ошибка", "Нет данных для экспорта!", QMessageBox.Icon.Warning)
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт пользователей",
            str(config.data_dir / f"{self.current_test.name}_users.csv"),
            "CSV файлы (*.csv)"
        )

        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Логин', 'Пароль', 'Использован'])

                    for login, password, used in self.current_test.credentials:
                        writer.writerow([login, password, 'Да' if used else 'Нет'])

                show_message(self, "Успех", f"Данные экспортированы в {file_path}")
            except Exception as e:
                show_message(self, "Ошибка", f"Ошибка экспорта: {str(e)}")

    def import_users(self): # Импорт пользователей из CSV
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Импорт пользователей",
            str(config.data_dir),
            "CSV файлы (*.csv)"
        )

        if file_path:
            try:
                import csv
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader)  # Пропускаем заголовок

                    for row in reader:
                        if len(row) >= 2:
                            login, password = row[0], row[1]
                            used = row[2].lower() == 'да' if len(row) > 2 else False
                            self.current_test.credentials.append((login, password, used))

                self.update_users_table()
                show_message(self, "Успех", "Пользователи импортированы!")
            except Exception as e:
                show_message(self, "Ошибка", f"Ошибка импорта: {str(e)}")

    def clear_users(self): # Очистка всех пользователей
        if not self.current_test.credentials:
            return

        reply = QMessageBox.question(
            self, "Очистка пользователей",
            "Удалить всех пользователей?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.current_test.credentials.clear()
            self.update_users_table()

    # === МЕТОДЫ ДЛЯ РАБОТЫ С РЕЗУЛЬТАТАМИ ===

    def view_results(self): # Просмотр результатов
        # Переключаемся на вкладку результатов
        tab_widget = self.centralWidget().findChild(QTabWidget)
        if tab_widget:
            tab_widget.setCurrentIndex(4)  # Вкладка результатов

    def refresh_results(self): # Обновление результатов
        test_filename = self.results_test_combo.currentData()
        if not test_filename:
            return

        # Загружаем результаты
        results = self.results_manager.get_test_results(test_filename)

        # Заполняем таблицу
        self.results_table.setRowCount(len(results))

        for i, result in enumerate(results):
            user_info = result['user_info']
            results_info = result['results']

            # Дата в удобном формате
            completed = datetime.fromisoformat(user_info['test_completed'])
            date_str = completed.strftime("%d.%m.%Y %H:%M")

            self.results_table.setItem(i, 0, QTableWidgetItem(user_info['login']))
            self.results_table.setItem(i, 1, QTableWidgetItem(date_str))
            self.results_table.setItem(i, 2, QTableWidgetItem(str(results_info['score_obtained'])))
            self.results_table.setItem(i, 3, QTableWidgetItem(str(results_info['max_achievable_score'])))
            self.results_table.setItem(i, 4, QTableWidgetItem(f"{results_info['percentage']:.1f}%"))
            self.results_table.setItem(i, 5, QTableWidgetItem(str(user_info['duration_seconds'] // 60) + " мин"))
            self.results_table.setItem(i, 6, QTableWidgetItem(str(user_info['duration_seconds'])))
            self.results_table.setItem(i, 7, QTableWidgetItem(os.path.basename(result['metadata']['saved_at'])))

        # Обновляем статистику
        stats = self.results_manager.get_statistics(test_filename)
        if stats:
            self.stats_total.setText(str(stats['total_attempts']))
            self.stats_avg_score.setText(f"{stats['average_score']:.1f}")
            self.stats_avg_percent.setText(f"{stats['average_percentage']:.1f}%")
            self.stats_best.setText(f"{stats['max_score']} ({stats['best_percentage']:.1f}%)")
            self.stats_worst.setText(f"{stats['min_score']} ({stats['worst_percentage']:.1f}%)")

    def update_results_test_combo(self): # Обновление списка тестов в комбобоксе результатов
        self.results_test_combo.clear()

        tests = config.get_test_list()
        for test in tests:
            self.results_test_combo.addItem(test['name'], test['filename'])

    def export_all_results(self): # Экспорт всех результатов
        test_filename = self.results_test_combo.currentData()
        if not test_filename:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт результатов",
            str(config.data_dir / f"{test_filename}_results.csv"),
            "CSV файлы (*.csv)"
        )

        if file_path:
            if self.results_manager.export_to_csv(test_filename, file_path):
                show_message(self, "Успех", f"Результаты экспортированы в {file_path}")
            else:
                show_message(self, "Ошибка", "Не удалось экспортировать результаты!")

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===

    def load_tests_list(self): # Загрузка списка тестов
        self.tests_list.clear()

        tests = config.get_test_list()
        for test in tests:
            icon = "🔒" if test['is_compiled'] else "📄"
            item = QListWidgetItem(f"{icon} {test['name']}")
            item.setData(Qt.ItemDataRole.UserRole, test['path'])
            self.tests_list.addItem(item)

    def load_selected_test(self): # Загрузка выбранного теста из списка
        item = self.tests_list.currentItem()
        if item:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            self.load_test_from_path(file_path)

    def show_test_context_menu(self, position): # Показать контекстное меню для теста
        item = self.tests_list.itemAt(position)
        if not item:
            return

        menu = QMenu()

        load_action = menu.addAction("📂 Загрузить")
        delete_action = menu.addAction("🗑️ Удалить")
        compile_action = menu.addAction("🔒 Скомпилировать")

        action = menu.exec(self.tests_list.mapToGlobal(position))

        if action == load_action:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            self.load_test_from_path(file_path)
        elif action == delete_action:
            self.delete_test(item)
        elif action == compile_action:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path.endswith('.xml'):
                if compile_selected_test(file_path):
                    self.load_tests_list()

    def delete_test(self, item): # Удаление теста
        file_path = item.data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self, "Удаление теста",
            f"Удалить тест '{os.path.basename(file_path)}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(file_path)
                self.load_tests_list()
                self.statusBar().showMessage(f"Тест удален: {os.path.basename(file_path)}")
            except Exception as e:
                show_message(self, "Ошибка", f"Не удалось удалить тест: {str(e)}")

    def save_test_info(self): # Сохранение информации о тесте
        self.save_test_info_from_ui()
        self.update_test_info_display()
        show_message(self, "Сохранение", "Информация о тесте сохранена!")

    def open_settings(self):
        """Открытие настроек"""
        from admin_auth import ChangePasswordDialog
        dialog = ChangePasswordDialog(self)
        dialog.exec()

    def show_about(self): # Показать информацию о программе
        about_text = """
        <h2>Конструктор Учебных Тестов (КУТ)</h2>
        <p><b>Версия 1.0</b></p>
        <p>Разработано для педагогической практики</p>
        <p><b>НИУ "МЭИ"</b></p>
        <p>Кафедра физики им. В.А. Фабриканта</p>
        <hr>
        <p><b>Функции:</b></p>
        <ul>
        <li>Создание тестов с разными типами вопросов</li>
        <li>Поддержка изображений и формул</li>
        <li>Генерация логинов и паролей</li>
        <li>Компиляция тестов для защиты</li>
        <li>Просмотр результатов тестирования</li>
        <li>Офлайн работа без базы данных</li>
        </ul>
        <hr>
        <p>© 2025 НИУ "МЭИ"</p>
        """

        QMessageBox.about(self, "О программе КУТ", about_text)

    def closeEvent(self, event): # Обработка закрытия окна
        if self.current_test and self.current_test.name:
            reply = QMessageBox.question(
                self, "Закрытие",
                "Сохранить текущий тест перед выходом?",
                QMessageBox.StandardButton.Yes |
                QMessageBox.StandardButton.No |
                QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            elif reply == QMessageBox.StandardButton.Yes:
                if not self.save_test():
                    event.ignore()
                    return

        event.accept()


# Дополнительные импорты
import csv