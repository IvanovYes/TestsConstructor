
# config.py - Конфигурация системы и управление путями

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any


class Config:
    """Класс для управления конфигурацией системы"""

    def __init__(self):
        # Определяем базовый путь
        if getattr(sys, 'frozen', False):
            # Режим .exe
            self.base_dir = Path(sys.executable).parent
        else:
            # Режим разработки
            self.base_dir = Path(__file__).parent

        # Пути к папкам данных
        self.data_dir = self.base_dir / "data"
        self.tests_dir = self.data_dir / "tests"
        self.results_dir = self.data_dir / "results"
        self.images_dir = self.data_dir / "images"
        self.config_file = self.data_dir / "config.ini"

        # Создаём структуру папок
        self.create_directories()

        # Загружаем конфигурацию
        self.settings = self.load_config()

    def create_directories(self):
        """Создание структуры папок"""
        directories = [
            self.data_dir,
            self.tests_dir,
            self.results_dir,
            self.images_dir
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации из файла"""
        default_config = {
            "admin": {
                "username": "admin",
                "password": "admin123"
            },
            "app": {
                "version": "1.0",
                "theme": "light",
                "language": "ru"
            },
            "testing": {
                "default_time_limit": 60,
                "default_max_score": 100,
                "show_hints": True
            }
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                # Если ошибка чтения, создаём новый
                self.save_config(default_config)
                return default_config
        else:
            self.save_config(default_config)
            return default_config

    def save_config(self, config: Dict[str, Any] = None):
        """Сохранение конфигурации в файл"""
        if config is None:
            config = self.settings

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.settings = config
            return True
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
            return False

    def get_admin_credentials(self) -> tuple:
        """Получение логина и пароля администратора"""
        admin = self.settings.get("admin", {})
        return admin.get("username", "admin"), admin.get("password", "admin123")

    def update_admin_password(self, new_password: str):
        """Обновление пароля администратора"""
        if "admin" not in self.settings:
            self.settings["admin"] = {}

        self.settings["admin"]["password"] = new_password
        self.save_config()

    def get_test_list(self) -> list:
        """Получение списка доступных тестов"""
        tests = []

        for file in self.tests_dir.iterdir():
            if file.suffix in ['.xml', '.kut']:
                # Пытаемся получить метаданные теста
                try:
                    if file.suffix == '.kut':
                        from test_compiler import TestCompiler
                        compiler = TestCompiler()
                        temp_file = self.tests_dir / "temp_decrypt.xml"
                        if compiler.decompile_test(file, temp_file):
                            test_info = self.extract_test_info(temp_file)
                            temp_file.unlink(missing_ok=True)
                        else:
                            test_info = {"name": file.stem, "description": "Зашифрованный тест"}
                    else:
                        test_info = self.extract_test_info(file)

                    tests.append({
                        "filename": file.name,
                        "path": str(file),
                        "name": test_info.get("name", file.stem),
                        "description": test_info.get("description", ""),
                        "is_compiled": file.suffix == '.kut',
                        "size": file.stat().st_size
                    })
                except:
                    # Если не удалось прочитать, добавляем базовую информацию
                    tests.append({
                        "filename": file.name,
                        "path": str(file),
                        "name": file.stem,
                        "description": "",
                        "is_compiled": file.suffix == '.kut',
                        "size": file.stat().st_size
                    })

        # Сортируем по имени
        tests.sort(key=lambda x: x["name"].lower())
        return tests

    def extract_test_info(self, xml_file: Path) -> Dict[str, Any]:
        """Извлечение информации о тесте из XML файла"""
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(xml_file)
            root = tree.getroot()

            info = root.find("info")
            if info is not None:
                name_elem = info.find("name")
                desc_elem = info.find("description")

                return {
                    "name": name_elem.text if name_elem is not None else xml_file.stem,
                    "description": desc_elem.text if desc_elem is not None else ""
                }
        except:
            pass

        return {"name": xml_file.stem, "description": ""}

    def get_available_images(self) -> list:
        """Получение списка доступных изображений"""
        images = []
        extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']

        for file in self.images_dir.iterdir():
            if file.suffix.lower() in extensions:
                images.append({
                    "name": file.name,
                    "path": str(file),
                    "size": file.stat().st_size
                })

        return images


# Глобальный объект конфигурации
config = Config()