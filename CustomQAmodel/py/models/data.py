from torch import cumsum, tensor
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
import pytorch_lightning as pl
from transformers import T5Tokenizer
import numpy as np

class BaseDataset(Dataset):
    """
    Базовый класс для обработки наборов данных.
    Позволяет задавать правила формирования source_encoding и target_encoding через переопределение методов.
    """
    def __init__(self, data, tokenizer: T5Tokenizer, text_max_token_len: int = 512, summary_max_token_len: int = 32):
        self.data = data
        self.tokenizer = tokenizer
        self.text_max_token_len = text_max_token_len
        self.summary_max_token_len = summary_max_token_len

    def __len__(self):
        return len(self.data)

    def get_text_input(self, data_row):
        """
        Метод для формирования текста входа.
        Переопределяется в дочерних классах.
        """
        raise NotImplementedError("Метод get_text_input должен быть переопределен в дочернем классе.")

    def get_target_output(self, data_row):
        """
        Метод для формирования текста выхода.
        Переопределяется в дочерних классах.
        """
        raise NotImplementedError("Метод get_target_output должен быть переопределен в дочернем классе.")

    def __getitem__(self, index: int):
        data_row = self.data.iloc[index]

        # Формирование source_encoding
        source_encoding = self.tokenizer(
            self.get_text_input(data_row),
            max_length=self.text_max_token_len,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            add_special_tokens=True,
            return_tensors='pt'
        )

        # Формирование target_encoding
        target_encoding = self.tokenizer(
            self.get_target_output(data_row),
            max_length=self.summary_max_token_len,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            add_special_tokens=True,
            return_tensors='pt'
        )

        labels = target_encoding['input_ids']
        labels[labels == 0] = -100  # Заменяем padding токены на -100

        return dict(
            input_ids=source_encoding['input_ids'].squeeze(),
            attention_mask=source_encoding['attention_mask'].squeeze(),
            labels=labels.squeeze(),
            labels_attention_mask=target_encoding['attention_mask'].squeeze()
        )
        
class SquadQADataset(BaseDataset):
    def __init__(self, data, tokenizer: T5Tokenizer, text_max_token_len: int = 396, summary_max_token_len: int = 32):
        super().__init__(data, tokenizer, text_max_token_len, summary_max_token_len)        
    """
    Дочерний класс для работы с QA-данными.
    Формирует входные данные в формате: "[КОНТЕКСТ]{context}<sep>[ВОПРОС]{question}" и ответ: {answer_text}.
    """
    def get_text_input(self, data_row):
        return f"[КОНТЕКСТ]{data_row['context']}[ВОПРОС]{data_row['question']}"

    def get_target_output(self, data_row):
        return data_row['answer_text']
    
class DaNetQADataset(BaseDataset):
    def __init__(self, data, tokenizer: T5Tokenizer, text_max_token_len: int = 396, summary_max_token_len: int = 32):
        super().__init__(data, tokenizer, text_max_token_len, summary_max_token_len)  
    """
    Дочерний класс для работы с DaNetQA-данными.
    Формирует входные данные в формате: "[КОНТЕКСТ]{context}<sep>[ВОПРОС]{question}" и ответ: {answer_text}.
    """
    def get_text_input(self, data_row):
        return f"[КОНТЕКСТ]{data_row['context']}[ВОПРОС]{data_row['question']}"

    def get_target_output(self, data_row):
        return data_row['answer_text']

class CombinedDataset(Dataset):
    def __init__(self, datasets, weights):
        """
        Инициализация комбинированного датасета.

        :param datasets: Список отдельных датасетов.
        :param weights: Веса для каждого датасета.
        """
        self.datasets = datasets
        self.weights = weights
        self.total_size = sum(len(d) for d in datasets)
        self.dataset_lengths = [len(d) for d in datasets]

    def __len__(self):
        return self.total_size

    def __getitem__(self, idx):
        """
        Получение элемента из комбинированного датасета по индексу.
        """
        dataset_idx = self._get_dataset_index(idx)
        dataset = self.datasets[dataset_idx]
        local_idx = idx % self.dataset_lengths[dataset_idx]
        return dataset[local_idx]

    def _get_dataset_index(self, idx):
        """
        Определение индекса датасета на основе глобального индекса.
        """
        cumulative_sizes = [0] + list(cumsum(tensor(self.dataset_lengths), dim=0))
        for i, size in enumerate(cumulative_sizes[:-1]):
            if size <= idx < cumulative_sizes[i + 1]:
                return i
        raise IndexError("Индекс вне диапазона.")
    
class CombinedDataModule(pl.LightningDataModule):
    """
    Класс для объединения нескольких наборов данных (тренировочных, валидационных, тестовых)
    с возможностью применения взвешенного случайного семплирования. 
    Позволяет использовать разные датасеты (например, QA, SuperGLUE и др.) 
    в едином процессе обучения.

    Аргументы:
        tokenizer: Токенизатор для обработки текстовых данных.
        train_datasets: Список тренировочных датасетов.
        val_datasets: Список валидационных датасетов (по умолчанию None).
        test_datasets: Список тестовых датасетов (по умолчанию None).
        train_weights: Веса для тренировочных датасетов.
        val_weights: Веса для валидационных датасетов (по умолчанию None).
        test_weights: Веса для тестовых датасетов (по умолчанию None).
        train_batch_size: Размер батча для тренировочного набора (по умолчанию 16).
        eval_batch_size: Размер батча для валидационного и тестового наборов (по умолчанию 16).
        summary_max_token_len: Максимальная длина токенов ответа (по умолчанию 128).
        text_max_token_len: Максимальная длина токенов входного текста (по умолчанию 512).
        num_workers: Количество воркеров для загрузки данных (по умолчанию 8).        
        pin_memory: Ускоряет передачу данных между RAM и VRAM (по умолчанию False).
    """
    def __init__(self,
                 tokenizer,
                 train_datasets,
                 val_datasets=None,
                 test_datasets=None,
                 train_weights=None,
                 val_weights=None,
                 test_weights=None,
                 train_batch_size=8,
                 eval_batch_size=8,
                 summary_max_token_len=128,
                 text_max_token_len=512,
                 num_workers=8,
                 pin_memory = False):
        super().__init__()
        self.tokenizer = tokenizer
        self.train_datasets = train_datasets
        self.val_datasets = val_datasets
        self.test_datasets = test_datasets
        # Если веса не заданы, вычисляем их автоматически
        self.train_weights = train_weights if train_weights else self.compute_dataset_weights([len(d) for d in train_datasets])
        self.val_weights = val_weights if val_weights else self.compute_dataset_weights([len(d) for d in val_datasets]) if val_datasets else None
        self.test_weights = test_weights if test_weights else self.compute_dataset_weights([len(d) for d in test_datasets]) if test_datasets else None
        self.train_batch_size = train_batch_size
        self.eval_batch_size = eval_batch_size
        self.summary_max_token_len = summary_max_token_len #todo использовать значение
        self.text_max_token_len = text_max_token_len #todo использовать значение
        self.num_workers = num_workers
        self.pin_memory = pin_memory     

    def setup(self, stage=None):
        # Настройка тренировочного датасета и семплера
        if self.train_datasets and self.train_weights:
            self.train_dataset = CombinedDataset(self.train_datasets, self.train_weights)
            self.train_sampler = self.create_weighted_sampler(self.train_weights, [len(d) for d in self.train_datasets])
        else:
            self.train_dataset, self.train_sampler = None, None

        # Настройка валидационного датасета и семплера
        if self.val_datasets and self.val_weights:
            self.val_dataset = CombinedDataset(self.val_datasets, self.val_weights)
            self.val_sampler = self.create_weighted_sampler(self.val_weights, [len(d) for d in self.val_datasets])
        else:
            self.val_dataset, self.val_sampler = None, None

        # Настройка тестового датасета и семплера
        if self.test_datasets and self.test_weights:
            self.test_dataset = CombinedDataset(self.test_datasets, self.test_weights)
            self.test_sampler = self.create_weighted_sampler(self.test_weights, [len(d) for d in self.test_datasets])
        else:
            self.test_dataset, self.test_sampler = None, None

    def train_dataloader(self):
        if not self.train_dataset:
            return None
        return DataLoader(
            self.train_dataset,
            sampler=self.train_sampler,
            batch_size=self.train_batch_size,
            num_workers=self.num_workers,
            persistent_workers=self.num_workers > 0,
            pin_memory=self.pin_memory
        )

    def val_dataloader(self):
        if not self.val_dataset:
            return None
        return DataLoader(
            self.val_dataset,
            sampler=self.val_sampler,
            batch_size=self.eval_batch_size,
            num_workers=self.num_workers,
            persistent_workers=self.num_workers > 0,
            pin_memory=self.pin_memory
        )

    def test_dataloader(self):
        if not self.test_dataset:
            return None
        return DataLoader(
            self.test_dataset,
            sampler=self.test_sampler,
            batch_size=self.eval_batch_size,
            num_workers=self.num_workers,
            persistent_workers=self.num_workers > 0,
            pin_memory=self.pin_memory
        )
        
    @staticmethod
    def create_weighted_sampler(dataset_weights, dataset_lengths):
        """
        Создание WeightedRandomSampler для комбинированного датасета.

        :param dataset_weights: Веса для каждого датасета.
        :param dataset_lengths: Размеры каждого датасета.
        :return: WeightedRandomSampler.
        """
        weights = []
        for dataset_weight, dataset_length in zip(dataset_weights, dataset_lengths):
            weights.extend([dataset_weight] * dataset_length)
        
        sampler = WeightedRandomSampler(weights, num_samples=sum(dataset_lengths), replacement=True)
        return sampler
    
    @staticmethod
    def compute_dataset_weights(dataset_sizes, smoothing_factor=0.3):
        """
        Вычисляет оптимальные веса для датасетов с разными объемами данных.

        :param dataset_sizes: Список размеров (количества примеров) для каждого датасета.
        :param smoothing_factor: Коэффициент сглаживания (0 - полностью обратные веса, 1 - равные веса).
        :return: Нормализованный список весов.
        """
        dataset_sizes = np.array(dataset_sizes, dtype=np.float32)
        inv_sizes = 1.0 / (dataset_sizes + 1e-6)  # Обратные размеры, избегаем деления на 0
        smoothed_weights = inv_sizes ** smoothing_factor  # Сглаживаем веса (уменьшаем крайние различия)
        return (smoothed_weights / smoothed_weights.sum()).tolist()  # Нормализация
