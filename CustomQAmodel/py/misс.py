import json
import pandas as pd
from transformers import T5Tokenizer
from typing import Callable, Any, Union, List
import torch
from torch.utils.data import DataLoader

# Загрузка набора данных SBERQUAD
def extract_sbsq(data:Any, tokenizer: T5Tokenizer = None, max_context_token_len: int = None):
    """
    Функции извлечения данных из структуры sbsq
    """
    questions = data[0]['data'][0]['paragraphs']
    data_rows = []
    for question in questions:
        context = question["context"]
        # Подсчет длины токенов контекста (если токенизатор указан)
        context_token_len = None if tokenizer is None else len(tokenizer(context).input_ids)
        
        # Пропускаем слишком длинные контексты
        if max_context_token_len != None and context_token_len > max_context_token_len:
            continue
        
        for question_and_answers in question["qas"]:
            question = question_and_answers["question"]
            # Подсчет длины токенов вопроса
            question_token_len = None if tokenizer is None else len(tokenizer(question).input_ids)
            
            if max_context_token_len != None and context_token_len + question_token_len > max_context_token_len:
                continue
            
            answers = question_and_answers["answers"]
            
            for answer in answers:
                answer_text = answer["text"]
                
                answer_start = answer["answer_start"]
                answer_end = answer_start + len(answer_text)
                
                # Добавление данных в список
                data_rows.append({
                    "question": question,
                    "context": context,
                    "answer_text": answer_text,
                    "answer_start": answer_start,
                    "answer_end": answer_end,
                    "question_token_len": question_token_len,
                    "context_token_len": context_token_len
                })
    return data_rows

def extract_daNetQA(data:Any, tokenizer: T5Tokenizer = None, max_context_token_len: int = None):
    """
    Функции извлечения данных из структуры daNetQA
    """
    data_rows = []  
    
    for line in data:
        context = line['passage']
        question = line['question']
        answer_text = 'да' if line['label'] else 'нет'
        context_token_len = None if tokenizer is None else len(tokenizer(context).input_ids)
        question_token_len = None if tokenizer is None else len(tokenizer(question).input_ids)
        
        if max_context_token_len != None and context_token_len + question_token_len > max_context_token_len:
                continue
        
        # Добавление данных в список
        data_rows.append({
            "context": context,
            "question": question,
            "answer_text": answer_text,
            "context_token_len": context_token_len,
            "question_token_len": question_token_len
            })
    return data_rows

class JSONDataLoader:
    """
    Универсальный загрузчик данных из JSON в DataFrame с использованием пользовательских правил извлечения.
    """
    def __init__(self, tokenizer: T5Tokenizer = None, max_text_token_len: int = None):
        """        
        :param tokenizer: Токенизатор для обработки текста (опционально).  
        :param max_context_token_len: Максимальная длина контекста в токенах.
        """
        self.max_text_token_len = max_text_token_len
        self.tokenizer = tokenizer

    def load_from_file(self, extraction_function: Callable[[Any, T5Tokenizer, int], dict], file_path: str) -> pd.DataFrame:
        """
        Загрузка данных из файла JSON или JSONL.
        :param extraction_function: Функция для извлечения данных.
        :param file_path: Путь к JSON-файлу.
        :return: DataFrame с извлеченными данными.
        """
        data = []
        try:
            with open(file_path, encoding='utf-8') as f:
                if file_path.endswith('.jsonl'):
                    # Чтение файла как JSONL (каждая строка — отдельный объект)
                    for line_number, line in enumerate(f, start=1):
                        try:
                            data.append(json.loads(line.strip()))  # Преобразуем каждую строку в объект
                        except json.JSONDecodeError as e:
                            print(f"Ошибка в строке {line_number}: {e}")
                elif file_path.endswith('.json'):
                    # Чтение всего содержимого как обычный JSON
                    raw_data = f.read()
                    data = json.loads(raw_data)
                    # Если это обычный массив объектов, преобразуем его в список
                    if isinstance(data, dict):
                        data = [data]
                else:
                    raise ValueError("Неподдерживаемый формат файла")
        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
        
        # Обработка данных с использованием extraction_function
        return pd.DataFrame(extraction_function(data, self.tokenizer, self.max_text_token_len))
    
def find_max_batch_size(model, dataloader:DataLoader, start_batch_size=16, step=2, max_attempts=10):
    """
    Определяет максимальный BATCH_SIZE, который помещается в память GPU.

    :param model: Нейросеть (PyTorch).
    :param dataloader: DataLoader с одним батчем.
    :param start_batch_size: Начальный размер батча.
    :param step: Увеличение размера батча на каждой итерации.
    :param max_attempts: Максимальное число попыток.
    :return: Оптимальный BATCH_SIZE.
    """
    batch_size = start_batch_size
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    
    for _ in range(max_attempts):
        try:
            sample_batch = next(iter(dataloader))
            sample_batch = {k: v.to(device) for k, v in sample_batch.items()}
            
            model(**sample_batch)  # Прогон через модель
            torch.cuda.empty_cache()
            
            batch_size *= step  # Увеличиваем размер
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                torch.cuda.empty_cache()
                return batch_size // step  # Возвращаем предыдущее значение
            else:
                raise e

    return batch_size

