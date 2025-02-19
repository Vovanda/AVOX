import torch
import pytorch_lightning as pl
from transformers import T5ForConditionalGeneration, T5Tokenizer
from torch.optim import AdamW
from torch.optim.lr_scheduler import LambdaLR

class QAModule(pl.LightningModule):
    def __init__(self, 
                 model: T5ForConditionalGeneration,
                 tokenizer: T5Tokenizer,
                 lr: float = 1e-5,
                 weight_decay: float = 1e-5):
        """
        Класс PyTorch Lightning модуля для обучения модели T5 для задач генерации текста.

        :param model: Предобученная модель T5ForConditionalGeneration
        :param tokenizer: Токенайзер модели T5
        :param lr: Скорость обучения
        :param weight_decay: Коэффициент регуляризации (L2)
        """
        super().__init__()
        self.model = model
        self.tokenizer = tokenizer
        self.learning_rate = lr
        self.weight_decay = weight_decay    

    def forward(self, input_ids, attention_mask, labels=None):
        """
        Прямой проход модели.

        :param input_ids: Токены входного текста
        :param attention_mask: Маска внимания
        :param labels: Токены целевого текста (для обучения)
        :return: Потери (loss) и логиты (logits)
        """
        output = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )
        return output.loss, output.logits    

    def training_step(self, batch, batch_idx):
        """
        Шаг обучения. Вычисляет loss, логирует метрики и возвращает значение потерь.

        :param batch: Батч данных, содержащий input_ids, attention_mask и labels.
        :param batch_idx: Индекс текущего батча в эпохе.
        :return: Значение потерь (loss).
        
        Логируемые метрики:
        - train_loss: Значение функции потерь на текущем батче.
        - grad_norm: Норма градиента для контроля переобучения/нестабильности.
        - lr: Текущий learning rate (если используется lr_scheduler).
        - gpu_mem: Использование памяти GPU в мегабайтах.
        """
        loss, logits = self(batch["input_ids"], batch["attention_mask"], batch["labels"])
        
        # Логируем loss
        self.log("train_loss", loss, on_epoch=True, on_step=True, prog_bar=True)

        # Логируем норму градиента
        grad_norm = torch.nn.utils.clip_grad_norm_(self.parameters(), max_norm=1e9)
        self.log("grad_norm", grad_norm, on_epoch=True, on_step=True, prog_bar=True)

        # Логируем learning rate
        lr = self.trainer.optimizers[0].param_groups[0]['lr']
        self.log("lr", lr, on_epoch=True, on_step=True, prog_bar=True)

        # Логируем использование памяти GPU
        if torch.cuda.is_available():
            self.log("gpu_mem", torch.cuda.memory_allocated() / 1024 ** 2, on_epoch=True, on_step=True)

        return loss


    def validation_step(self, batch, batch_idx):
        """
        Шаг валидации. Используется для оценки модели на валидационных данных.

        :param batch: Батч данных
        :param batch_idx: Индекс батча
        :return: Значение потерь (loss)
        """
        labels = batch["labels"]
        loss, logits = self(batch["input_ids"], batch["attention_mask"], labels)
        self.log("val_loss", loss, on_epoch=True, on_step=False)  # Логируем только на эпохе
        return loss 

    def test_step(self, batch, batch_idx):
        """
        Шаг тестирования. Логируется loss и декодируются предсказания модели.

        :param batch: Батч данных
        :param batch_idx: Индекс батча
        :return: Словарь с потерями и предсказаниями
        """        
        loss, logits = self(batch["input_ids"], batch["attention_mask"], batch["labels"])
        # Декодируем предсказания в текст
        predictions = self.tokenizer.batch_decode(logits.argmax(dim=-1), skip_special_tokens=True)
        self.log("test_loss", loss, on_epoch=True, prog_bar=True)  # Логируем test loss
        return {"loss": loss, "predictions": predictions}

    def configure_optimizers(self):    
        """
        Настройка оптимизатора и планировщика скорости обучения.

        :return: Список с оптимизатором и планировщиком
        """
        optimizer = AdamW(self.parameters(), lr=self.learning_rate, weight_decay=self.weight_decay)
        # Линейный спад скорости обучения с коэффициентом 0.95
        scheduler = LambdaLR(optimizer, lambda epoch: 0.95 ** epoch)
        return [optimizer], [scheduler]