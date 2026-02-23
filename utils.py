
# utils.py - Вспомогательные классы и функции

import os
import random
import string
import xml.etree.ElementTree as ET
from datetime import datetime
from PyQt6.QtCore import Qt
from config import config
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from PyQt6.QtGui import QPixmap


@dataclass
class TestQuestion: # Класс вопроса теста
    id: int = 0
    text: str = ""
    question_type: str = "single"  # single/multiple/text
    options: List[str] = field(default_factory=list)
    correct_answers: List[int] = field(default_factory=list)
    points: int = 1
    image_path: str = ""
    block_id: int = 0


@dataclass
class TestBlock: # Класс блока вопросов
    id: int = 0
    name: str = ""
    questions: List[TestQuestion] = field(default_factory=list)
    random_count: int = 1
    min_questions: int = 1
    max_questions: int = 5


@dataclass
class TestConfig: # Класс конфигурации теста
    filename: str = ""
    name: str = ""
    description: str = ""
    max_score: int = 100
    time_limit: int = 60
    blocks: List[TestBlock] = field(default_factory=list)
    mix_questions: bool = False
    credentials: List[Tuple[str, str, bool]] = field(default_factory=list)  # (login, password, used)
    is_compiled: bool = False
    compile_date: Optional[datetime] = None
    usage_count: int = 0
    last_used: Optional[datetime] = None

    def mark_login_used(self, login: str) -> bool: # Пометить логин как использованный
        for i, (l, p, u) in enumerate(self.credentials):
            if l == login and not u:
                self.credentials[i] = (l, p, True)
                self.usage_count += 1
                self.last_used = datetime.now()
                return True
        return False

    def get_unused_logins(self) -> List[Tuple[str, str]]:
        # Получить неиспользованные логины
        return [(l, p) for l, p, u in self.credentials if not u]

    def get_used_logins(self) -> List[Tuple[str, str, datetime]]:
        # Получить использованные логины
        return [(l, p, self.last_used) for l, p, u in self.credentials if u]

    def add_credentials(self, count: int, prefix: str = "student") -> List[Tuple[str, str]]:
        # Добавить новые логины/пароли
        self.credentials.clear()
        for i in range(1, count + 1):
            login = f"{prefix}_{i:03d}"
            password = generate_password(10)
            self.credentials.append((login, password, False))


    def remove_credentials(self, login: str) -> bool: # Удалить логин/пароль
        for i, (l, p, u) in enumerate(self.credentials):
            if l == login:
                self.credentials.pop(i)
                return True
        return False


def generate_password(length: int = 10) -> str:
    # Генерация случайного пароля
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def save_test_to_xml(test_config: TestConfig, file_path: str) -> bool:
    # Сохранение теста в XML файл
    try:
        root = ET.Element("test")

        # Основная информация
        info = ET.SubElement(root, "info")
        ET.SubElement(info, "name").text = test_config.name
        ET.SubElement(info, "description").text = test_config.description
        ET.SubElement(info, "max_score").text = str(test_config.max_score)
        ET.SubElement(info, "time_limit").text = str(test_config.time_limit)
        ET.SubElement(info, "mix_questions").text = str(test_config.mix_questions)
        ET.SubElement(info, "created").text = datetime.now().isoformat()

        # Аутентификация (логины/пароли)
        if test_config.credentials:
            auth = ET.SubElement(root, "authentication")
            users = ET.SubElement(auth, "users")

            for login, password, used in test_config.credentials:
                user = ET.SubElement(users, "user")
                user.set("login", login)
                user.set("password", password)
                user.set("used", str(used).lower())

        # Статистика
        stats = ET.SubElement(root, "statistics")
        ET.SubElement(stats, "usage_count").text = str(test_config.usage_count)
        if test_config.last_used:
            ET.SubElement(stats, "last_used").text = test_config.last_used.isoformat()

        # Блоки вопросов
        blocks_elem = ET.SubElement(root, "blocks")

        for block in test_config.blocks:
            block_elem = ET.SubElement(blocks_elem, "block")
            block_elem.set("id", str(block.id))
            block_elem.set("name", block.name)
            block_elem.set("random_count", str(block.random_count))

            # Вопросы блока
            questions_elem = ET.SubElement(block_elem, "questions")

            for question in block.questions:
                q_elem = ET.SubElement(questions_elem, "question")
                q_elem.set("id", str(question.id))
                q_elem.set("type", question.question_type)
                q_elem.set("points", str(question.points))
                q_elem.set("block_id", str(question.block_id))

                ET.SubElement(q_elem, "text").text = question.text

                if question.image_path:
                    ET.SubElement(q_elem, "image_path").text = question.image_path

                # Варианты ответов
                if question.options:
                    options_elem = ET.SubElement(q_elem, "options")
                    for opt in question.options:
                        ET.SubElement(options_elem, "option").text = opt

                # Правильные ответы
                if question.correct_answers:
                    correct_elem = ET.SubElement(q_elem, "correct_answers")
                    for ans in question.correct_answers:
                        ET.SubElement(correct_elem, "answer").text = str(ans)

        # Форматирование XML
        from xml.dom import minidom
        xml_str = ET.tostring(root, encoding='utf-8')
        parsed = minidom.parseString(xml_str)
        pretty_xml = parsed.toprettyxml(indent="  ", encoding='utf-8')

        # Сохранение
        with open(file_path, 'wb') as f:
            f.write(pretty_xml)

        return True

    except Exception as e:
        print(f"Ошибка сохранения теста: {e}")
        return False


def load_test_from_xml(file_path: str) -> Optional[TestConfig]:
    # Загрузка теста из XML файла
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Создаём конфигурацию
        test_config = TestConfig()
        test_config.filename = os.path.basename(file_path)

        # Основная информация
        info = root.find("info")
        if info is not None:
            test_config.name = info.find("name").text or ""
            test_config.description = info.find("description").text or ""

            max_score = info.find("max_score")
            if max_score is not None:
                test_config.max_score = int(max_score.text)

            time_limit = info.find("time_limit")
            if time_limit is not None:
                test_config.time_limit = int(time_limit.text)

            mix_questions = info.find("mix_questions")
            if mix_questions is not None:
                test_config.mix_questions = mix_questions.text.lower() == "true"

        # Аутентификация
        auth = root.find("authentication")
        if auth is not None:
            users = auth.find("users")
            if users is not None:
                for user_elem in users.findall("user"):
                    login = user_elem.get("login", "")
                    password = user_elem.get("password", "")
                    used = user_elem.get("used", "false").lower() == "true"
                    test_config.credentials.append((login, password, used))

        # Статистика
        stats = root.find("statistics")
        if stats is not None:
            usage_count = stats.find("usage_count")
            if usage_count is not None:
                test_config.usage_count = int(usage_count.text)

            last_used = stats.find("last_used")
            if last_used is not None and last_used.text:
                try:
                    test_config.last_used = datetime.fromisoformat(last_used.text)
                except:
                    pass

        # Блоки вопросов
        blocks_elem = root.find("blocks")
        if blocks_elem is not None:
            for block_elem in blocks_elem.findall("block"):
                block = TestBlock()
                block.id = int(block_elem.get("id", "0"))
                block.name = block_elem.get("name", f"Блок {block.id}")
                block.random_count = int(block_elem.get("random_count", "1"))

                # Вопросы
                questions_elem = block_elem.find("questions")
                if questions_elem is not None:
                    for q_elem in questions_elem.findall("question"):
                        question = TestQuestion()
                        question.id = int(q_elem.get("id", "0"))
                        question.question_type = q_elem.get("type", "single")
                        question.points = int(q_elem.get("points", "1"))
                        question.block_id = int(q_elem.get("block_id", str(block.id)))

                        text_elem = q_elem.find("text")
                        if text_elem is not None:
                            question.text = text_elem.text or ""

                        image_elem = q_elem.find("image_path")
                        if image_elem is not None and image_elem.text:
                            question.image_path = image_elem.text

                        # Варианты ответов
                        options_elem = q_elem.find("options")
                        if options_elem is not None:
                            for opt_elem in options_elem.findall("option"):
                                if opt_elem.text:
                                    question.options.append(opt_elem.text)

                        # Правильные ответы
                        correct_elem = q_elem.find("correct_answers")
                        if correct_elem is not None:
                            for ans_elem in correct_elem.findall("answer"):
                                try:
                                    question.correct_answers.append(int(ans_elem.text))
                                except:
                                    pass

                        block.questions.append(question)

                test_config.blocks.append(block)

        return test_config

    except Exception as e:
        print(f"Ошибка загрузки теста: {e}")
        return None


def show_message(parent, title: str, message: str,
                 icon=QMessageBox.Icon.Information) -> None:
    # Показать диалоговое окно с сообщением
    msg = QMessageBox(parent)
    msg.setIcon(icon)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()


def browse_image(parent, current_path: str = "") -> str:
    # Открыть диалог выбора изображения
    file_path, _ = QFileDialog.getOpenFileName(
        parent,
        "Выберите изображение",
        current_path or str(config.images_dir),
        "Изображения (*.png *.jpg *.jpeg *.bmp *.gif);;Все файлы (*.*)"
    )
    return file_path


def load_pixmap(image_path: str, max_width: int = 600, max_height: int = 400) -> Optional[QPixmap]:
    # Загрузка изображения с масштабированием
    if not image_path or not os.path.exists(image_path):
        return None

    try:
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return None

        # Масштабирование с сохранением пропорций
        pixmap = pixmap.scaled(
            max_width, max_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        return pixmap
    except:
        return None