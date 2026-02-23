"""
test_compiler.py - Компиляция и декомпиляция тестов
"""
import base64
import hashlib
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from config import config
from utils import save_test_to_xml, load_test_from_xml


class TestCompiler:
    """Класс для компиляции тестов в защищённый формат"""

    def __init__(self, master_password: str = "KUT_COMPILER_MASTER_KEY_2025"):
        self.master_password = master_password.encode()
        self.salt = b'KUT_SALT_VALUE_2025_MEPHI'
        self.key = self._derive_key()

    def _derive_key(self) -> bytes:
        """Создание ключа шифрования"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_password))
        return key

    def compile_test(self, xml_path: str, output_path: str = None) -> bool:
        """
        Компиляция теста в защищённый формат .kut

        Args:
            xml_path: Путь к XML файлу теста
            output_path: Путь для сохранения (если None, заменяет исходный)

        Returns:
            True если успешно, False в противном случае
        """
        try:
            # Загружаем тест
            test_config = load_test_from_xml(xml_path)
            if not test_config:
                return False

            # Читаем исходный XML
            with open(xml_path, 'r', encoding='utf-8') as f:
                xml_data = f.read()

            # Создаём заголовок с метаданными
            header = {
                'format': 'KUT_COMPILED',
                'version': '1.0',
                'original_name': test_config.name,
                'original_filename': test_config.filename,
                'compiled_at': datetime.now().isoformat(),
                'checksum': hashlib.sha256(xml_data.encode()).hexdigest()
            }

            # Шифруем данные
            fernet = Fernet(self.key)
            encrypted_data = fernet.encrypt(xml_data.encode())

            # Определяем путь для сохранения
            if output_path is None:
                output_path = xml_path.replace('.xml', '.kut')

            # Сохраняем скомпилированный файл
            with open(output_path, 'wb') as f:
                # Записываем длину заголовка
                header_json = json.dumps(header).encode('utf-8')
                f.write(len(header_json).to_bytes(4, 'big'))

                # Записываем заголовок
                f.write(header_json)

                # Записываем зашифрованные данные
                f.write(encrypted_data)

            # Обновляем конфигурацию теста
            test_config.is_compiled = True
            test_config.compile_date = datetime.now()
            test_config.filename = os.path.basename(output_path)

            # Сохраняем обратно (если нужно)
            # save_test_to_xml(test_config, xml_path)

            return True

        except Exception as e:
            print(f"Ошибка компиляции: {e}")
            return False

    def decompile_test(self, kut_path: str, output_path: str = None) -> bool:
        """
        Декомпиляция теста из формата .kut

        Args:
            kut_path: Путь к .kut файлу
            output_path: Путь для сохранения XML

        Returns:
            True если успешно, False в противном случае
        """
        try:
            with open(kut_path, 'rb') as f:
                # Читаем длину заголовка
                header_len_bytes = f.read(4)
                if len(header_len_bytes) < 4:
                    return False

                header_len = int.from_bytes(header_len_bytes, 'big')

                # Читаем заголовок
                header_json = f.read(header_len)
                if len(header_json) < header_len:
                    return False

                header = json.loads(header_json.decode('utf-8'))

                # Проверяем формат
                if header.get('format') != 'KUT_COMPILED':
                    return False

                # Читаем зашифрованные данные
                encrypted_data = f.read()

                # Дешифруем
                fernet = Fernet(self.key)
                xml_data = fernet.decrypt(encrypted_data).decode('utf-8')

                # Проверяем контрольную сумму
                if hashlib.sha256(xml_data.encode()).hexdigest() != header['checksum']:
                    return False

                # Определяем путь для сохранения
                if output_path is None:
                    # Сохраняем во временный файл
                    import tempfile
                    fd, output_path = tempfile.mkstemp(suffix='.xml')
                    os.close(fd)

                # Сохраняем XML
                with open(output_path, 'w', encoding='utf-8') as out_f:
                    out_f.write(xml_data)

                return True

        except Exception as e:
            print(f"Ошибка декомпиляции: {e}")
            return False

    def is_compiled(self, file_path: str) -> bool:
        """Проверка, является ли файл скомпилированным тестом"""
        try:
            with open(file_path, 'rb') as f:
                # Пытаемся прочитать заголовок
                header_len_bytes = f.read(4)
                if len(header_len_bytes) < 4:
                    return False

                header_len = int.from_bytes(header_len_bytes, 'big')
                header_json = f.read(header_len)

                if len(header_json) < header_len:
                    return False

                header = json.loads(header_json.decode('utf-8'))
                return header.get('format') == 'KUT_COMPILED'

        except:
            return False

    def get_compiled_info(self, kut_path: str) -> dict:
        """Получение информации о скомпилированном тесте"""
        try:
            with open(kut_path, 'rb') as f:
                header_len_bytes = f.read(4)
                if len(header_len_bytes) < 4:
                    return {}

                header_len = int.from_bytes(header_len_bytes, 'big')
                header_json = f.read(header_len)

                if len(header_json) < header_len:
                    return {}

                header = json.loads(header_json.decode('utf-8'))
                return header

        except:
            return {}


# Утилиты для работы с компилятором
def compile_selected_test(xml_file: str, show_progress=True) -> bool:
    """Компиляция выбранного теста с прогрессом"""
    compiler = TestCompiler()

    if show_progress:
        from PyQt6.QtWidgets import QProgressDialog
        from PyQt6.QtCore import Qt

        progress = QProgressDialog("Компиляция теста...", "Отмена", 0, 100)
        progress.setWindowTitle("Компиляция")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setValue(0)
        progress.show()

        # Имитация прогресса
        for i in range(101):
            progress.setValue(i)
            QApplication.processEvents()
            if progress.wasCanceled():
                return False
            import time
            time.sleep(0.01)

    result = compiler.compile_test(xml_file)

    if show_progress:
        progress.setValue(100)
        progress.close()

    return result


def decompile_for_editing(kut_file: str) -> str:
    """Декомпиляция теста для редактирования"""
    compiler = TestCompiler()

    # Создаём временный файл для редактирования
    import tempfile
    fd, temp_path = tempfile.mkstemp(suffix='.xml', prefix='edit_')
    os.close(fd)

    if compiler.decompile_test(kut_file, temp_path):
        return temp_path
    else:
        return ""


# Импорты для функций выше
import os
from datetime import datetime
from PyQt6.QtWidgets import QApplication