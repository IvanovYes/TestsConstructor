
# Управление результатами тестирования

import json
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import config


class ResultsManager:
    """Менеджер для работы с результатами тестирования"""

    def __init__(self):
        self.results_dir = config.results_dir

    def save_result(self, test_config, user_login: str, user_answers: Dict,
                    start_time: datetime, end_time: datetime) -> str:
        """
        Сохранение результата тестирования

        Args:
            test_config: Конфигурация теста
            user_login: Логин пользователя
            user_answers: Ответы пользователя
            start_time: Время начала
            end_time: Время окончания

        Returns:
            Путь к сохранённому файлу
        """
        # Подсчёт результатов
        score, max_score, percentage = self.calculate_score(test_config, user_answers)
        duration = (end_time - start_time).total_seconds()

        # Формирование данных
        result_data = {
            "test_info": {
                "filename": test_config.filename,
                "name": test_config.name,
                "description": test_config.description,
                "max_possible_score": test_config.max_score
            },
            "user_info": {
                "login": user_login,
                "test_started": start_time.isoformat(),
                "test_completed": end_time.isoformat(),
                "duration_seconds": int(duration)
            },
            "results": {
                "score_obtained": score,
                "max_achievable_score": max_score,
                "percentage": percentage,
                "questions_total": len(user_answers),
                "questions_answered": sum(1 for a in user_answers.values() if a['is_answered'])
            },
            "detailed_answers": self.prepare_detailed_answers(test_config, user_answers),
            "metadata": {
                "saved_at": datetime.now().isoformat(),
                "version": "1.0"
            }
        }

        # Создание имени файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_test_name = test_config.name.replace(" ", "_").replace("/", "_")
        safe_login = user_login.replace(" ", "_")
        filename = f"{safe_test_name}_{safe_login}_{timestamp}.json"
        filepath = self.results_dir / filename

        # Сохранение
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)

        return str(filepath)

    def calculate_score(self, test_config, user_answers: Dict) -> tuple:
        """Подсчёт баллов"""
        total_score = 0
        max_possible_score = 0

        # Собираем все вопросы из теста
        all_questions = []
        for block in test_config.blocks:
            all_questions.extend(block.questions)

        for q_idx, answer_data in user_answers.items():
            if q_idx < len(all_questions):
                question = all_questions[q_idx]
                max_possible_score += question.points

                if answer_data['is_answered']:
                    user_answer = answer_data['answer']

                    if question.question_type == "single":
                        if user_answer in question.correct_answers:
                            total_score += question.points

                    elif question.question_type == "multiple":
                        if set(user_answer) == set(question.correct_answers):
                            total_score += question.points
                        elif user_answer:  # Частичный балл
                            correct_count = len(set(user_answer) & set(question.correct_answers))
                            if correct_count > 0:
                                partial_score = (correct_count / len(question.correct_answers)) * question.points
                                total_score += partial_score

                    elif question.question_type == "text":
                        # Простая проверка (в реальной системе сложнее)
                        if str(user_answer).strip().lower() == str(question.correct_answers[0]).strip().lower():
                            total_score += question.points

        percentage = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
        return total_score, max_possible_score, percentage

    def prepare_detailed_answers(self, test_config, user_answers: Dict) -> List[Dict]:
        """Подготовка детализированных ответов"""
        detailed = []

        # Собираем все вопросы
        all_questions = []
        for block in test_config.blocks:
            all_questions.extend(block.questions)

        for q_idx, answer_data in user_answers.items():
            if q_idx < len(all_questions):
                question = all_questions[q_idx]

                detailed.append({
                    "question_id": question.id,
                    "question_text": question.text[:100] + "..." if len(question.text) > 100 else question.text,
                    "question_type": question.question_type,
                    "user_answer": str(answer_data['answer']),
                    "correct_answers": [str(a) for a in question.correct_answers] if question.correct_answers else [],
                    "is_correct": self.check_answer_correct(question, answer_data['answer']),
                    "points_possible": question.points
                })

        return detailed

    def check_answer_correct(self, question, user_answer) -> bool:
        """Проверка правильности ответа"""
        if question.question_type == "single":
            return user_answer in question.correct_answers
        elif question.question_type == "multiple":
            return set(user_answer) == set(question.correct_answers)
        elif question.question_type == "text":
            return str(user_answer).strip().lower() == str(question.correct_answers[0]).strip().lower()
        return False

    def get_test_results(self, test_filename: str) -> List[Dict]:
        """Получение всех результатов для конкретного теста"""
        results = []
        test_name = Path(test_filename).stem

        for result_file in self.results_dir.glob(f"{test_name}_*.json"):
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    results.append(data)
            except:
                continue

        # Сортировка по дате завершения
        results.sort(key=lambda x: x['user_info']['test_completed'], reverse=True)
        return results

    def get_all_results(self) -> List[Dict]:
        """Получение всех результатов"""
        results = []

        for result_file in self.results_dir.glob("*.json"):
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    results.append(data)
            except:
                continue

        return results

    def export_to_csv(self, test_filename: str, output_path: str) -> bool:
        """Экспорт результатов в CSV"""
        results = self.get_test_results(test_filename)

        if not results:
            return False

        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Заголовки
                writer.writerow([
                    'Логин', 'Тест', 'Дата начала', 'Дата завершения',
                    'Длительность (сек)', 'Набрано баллов', 'Макс. баллов',
                    'Процент', 'Отвечено вопросов', 'Всего вопросов'
                ])

                # Данные
                for result in results:
                    writer.writerow([
                        result['user_info']['login'],
                        result['test_info']['name'],
                        result['user_info']['test_started'],
                        result['user_info']['test_completed'],
                        result['user_info']['duration_seconds'],
                        result['results']['score_obtained'],
                        result['results']['max_achievable_score'],
                        f"{result['results']['percentage']:.1f}%",
                        result['results']['questions_answered'],
                        result['results']['questions_total']
                    ])

            return True

        except Exception as e:
            print(f"Ошибка экспорта в CSV: {e}")
            return False

    def delete_result(self, result_file: str) -> bool:
        """Удаление результата"""
        try:
            file_path = Path(result_file)
            if file_path.exists():
                file_path.unlink()
                return True
        except:
            pass
        return False

    def get_statistics(self, test_filename: str) -> Dict[str, Any]:
        """Получение статистики по тесту"""
        results = self.get_test_results(test_filename)

        if not results:
            return {}

        total_attempts = len(results)
        scores = [r['results']['score_obtained'] for r in results]
        max_scores = [r['results']['max_achievable_score'] for r in results]
        percentages = [r['results']['percentage'] for r in results]

        avg_score = sum(scores) / total_attempts if total_attempts > 0 else 0
        avg_percentage = sum(percentages) / total_attempts if total_attempts > 0 else 0
        max_score = max(scores) if scores else 0
        min_score = min(scores) if scores else 0

        return {
            "total_attempts": total_attempts,
            "average_score": round(avg_score, 2),
            "average_percentage": round(avg_percentage, 2),
            "max_score": max_score,
            "min_score": min_score,
            "best_percentage": max(percentages) if percentages else 0,
            "worst_percentage": min(percentages) if percentages else 0
        }