# %%
%load_ext tensorboard

# %%
from py.misс import JSONDataLoader, extract_sbsq, extract_daNetQA, find_max_batch_size
from py.models.data import SquadQADataset, DaNetQADataset, CombinedDataModule
from transformers import T5Tokenizer

# Определяем оптимальный BATCH_SIZE


MODEL_NAME = "ai-forever/ruT5-base"

# Оптимальный BATCH_SIZE зависит от памяти GPU:
# - RTX 3090 (24GB VRAM):
#   - T5-small → 32–64
#   - T5-base → 16–32
#   - T5-large → 8–16
#   - T5-3B → 2–4
# Используйте `find_max_batch_size()` для точного подбора.
# Малый батч (≤16): более шумный градиент, но лучшее обобщение.
# Большой батч (≥64): более стабильный градиент, но может переобучаться.
# При нехватке памяти → уменьшите batch_size или включите gradient accumulation.
BATCH_SIZE = 8
N_EPOCHS = 3

# Загрузка токенизатора
special_tokens = {'additional_special_tokens': ['[КОНТЕКСТ]', '[ВОПРОС]']}
tokenizer: T5Tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME, legacy=False)
tokenizer.add_special_tokens(special_tokens)

# Максимальная длина токенов
MAX_TEXT_TOKEN_LEN = 1024

json_data_loader = JSONDataLoader(tokenizer = tokenizer, max_text_token_len = MAX_TEXT_TOKEN_LEN)

# %%
# Загрузка тренировочного набора данных sberquad
squad_df = json_data_loader.load_from_file(extraction_function = extract_sbsq, file_path="datasets\\sberquad\\train_v1.0\\train_v1.0.json")
squad_dataset = SquadQADataset(squad_df, tokenizer=tokenizer, text_max_token_len=MAX_TEXT_TOKEN_LEN, summary_max_token_len=1024)
# Загрузка валидационного набора данных sberquad
val_squad_df = json_data_loader.load_from_file(extraction_function = extract_sbsq, file_path="datasets\\sberquad\\dev_v1.0\\dev_v1.0.json")
val_squad_dataset = SquadQADataset(val_squad_df, tokenizer=tokenizer, text_max_token_len=MAX_TEXT_TOKEN_LEN, summary_max_token_len=1024)

# %%
# Загрузка тренировочного набора данных sberquad DaNetQA
daNetQA_df = json_data_loader.load_from_file(extraction_function = extract_daNetQA, file_path="datasets\\RussianSuperGlue\\DaNetQA\\train.jsonl")
daNetQA_dataset = DaNetQADataset(daNetQA_df, tokenizer=tokenizer, text_max_token_len=MAX_TEXT_TOKEN_LEN, summary_max_token_len=1024)
# Загрузка валидационного набора данных DaNetQA
val_daNetQA_df = json_data_loader.load_from_file(extraction_function = extract_daNetQA, file_path="datasets\\RussianSuperGlue\\DaNetQA\\val.jsonl")
val_daNetQA_dataset = SquadQADataset(val_daNetQA_df, tokenizer=tokenizer, text_max_token_len=MAX_TEXT_TOKEN_LEN, summary_max_token_len=1024)

# %%
# Инициализация DataModule
train_dataloader = CombinedDataModule(
    tokenizer=tokenizer,
    train_datasets=[squad_dataset, daNetQA_dataset],
    val_datasets=[val_squad_dataset, val_daNetQA_dataset],
    train_batch_size=BATCH_SIZE,
    eval_batch_size=BATCH_SIZE,
    num_workers=8,
    persistent_workers=True
)

# Настройка DataLoader
train_dataloader.setup(stage='fit')

# %%
train_dataloader.train_weights

# %%
[len(squad_dataset.data), len(daNetQA_dataset.data)]

# %%
from py.models.model import QAModule
import pytorch_lightning as pl
from pytorch_lightning.loggers import TensorBoardLogger
from pytorch_lightning.callbacks import (ModelCheckpoint, EarlyStopping)
from transformers import T5ForConditionalGeneration

import torch
#pl.seed_everything(42, workers=True)

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
t5_model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME, return_dict=True)
model = QAModule(t5_model, lr=1e-4, weight_decay=1e-5)
model.to(device)

torch.set_float32_matmul_precision('high')

tb_logger = TensorBoardLogger('logs', name="t5_qa",)

checkpoint_callback = ModelCheckpoint(
    monitor="val_loss",
    dirpath="checkpoints",
    filename="best_model-{epoch:02d}-{val_loss:.2f}",
    save_top_k=1,
    mode="min",
    every_n_epochs=1,
    verbose=True
)

early_stopping_callback = EarlyStopping(
    monitor="val_loss",
    patience=3,  # Количество эпох без улучшения до остановки
    mode="min",
    verbose=True
)

trainer = pl.Trainer(
    callbacks=[checkpoint_callback, early_stopping_callback],
    logger=tb_logger,
    max_epochs=N_EPOCHS,
    accelerator="gpu",
    devices=1,
    log_every_n_steps=1,
    accumulate_grad_batches=8, #накапливать каждые 8 батча (эффективный batch size — batch_size*8)
    precision="16-mixed" # Используем смешанную точность
)



# %%
trainer.fit(model, train_dataloader)

# %%
trainer.validate(model, train_dataloader)

# %%
trainer.test(datamodule=train_dataloader)


