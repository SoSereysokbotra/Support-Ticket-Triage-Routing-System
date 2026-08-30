import json
import os
import sys
from pathlib import Path
from typing import Dict

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from datasets import Dataset
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
from sklearn.utils.class_weight import compute_class_weight
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)

from src.domain.entities.category import TicketCategory
from src.infrastructure.data.dataset_loader import DatasetLoader


class WeightedTrainer(Trainer):
    """
    Custom Trainer that incorporates inverse class frequency weights
    into the CrossEntropyLoss to combat class imbalance in ticket categories.
    """

    def __init__(self, class_weights: torch.Tensor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")

        loss_fct = nn.CrossEntropyLoss(weight=self.class_weights.to(model.device))
        loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))
        return (loss, outputs) if return_outputs else loss


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    macro_f1 = f1_score(labels, preds, average="macro")
    weighted_f1 = f1_score(labels, preds, average="weighted")
    acc = accuracy_score(labels, preds)
    return {
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "accuracy": round(acc, 4),
    }


def train_model(
    model_name: str = "distilbert-base-uncased",
    output_dir: Path | None = None,
    num_epochs: int = 4,
    batch_size: int = 16,
    learning_rate: float = 3e-5,
    max_length: int = 128,
) -> Dict[str, float]:
    project_root = Path(__file__).resolve().parents[3]
    output_dir = output_dir or (project_root / "models" / "distilbert_v0")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("PHASE 0: Fine-Tuning DistilBERT Baseline Ticket Classifier")
    print("=" * 60)

    # 1. Load Data
    loader = DatasetLoader()
    train_df, val_df, test_df = loader.get_stratified_splits()
    print(f"Dataset split sizes: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")

    # 2. Build Label Mappings
    categories = [cat.value for cat in TicketCategory]
    label2id = {label: i for i, label in enumerate(categories)}
    id2label = {i: label for i, label in enumerate(categories)}

    # Map labels to integers
    train_df["label"] = train_df["category"].map(label2id)
    val_df["label"] = val_df["category"].map(label2id)
    test_df["label"] = test_df["category"].map(label2id)

    # 3. Calculate Class Weights for Imbalance Handling
    classes_present = np.unique(train_df["label"])
    weights = compute_class_weight(
        class_weight="balanced",
        classes=classes_present,
        y=train_df["label"].to_numpy(),
    )
    # Ensure full weight tensor matching num_labels
    full_weights = np.ones(len(categories), dtype=np.float32)
    for c_idx, w in zip(classes_present, weights):
        full_weights[c_idx] = w
    class_weights_tensor = torch.tensor(full_weights, dtype=torch.float32)
    print(f"Calculated Class Weights: {dict(zip(categories, np.round(full_weights, 3)))}")

    # 4. Tokenization
    print(f"Loading base tokenizer '{model_name}'...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def tokenize_fn(batch):
        return tokenizer(batch["text"], truncation=True, max_length=max_length)

    train_ds = Dataset.from_pandas(train_df[["text", "label"]])
    val_ds = Dataset.from_pandas(val_df[["text", "label"]])
    test_ds = Dataset.from_pandas(test_df[["text", "label"]])

    train_tokenized = train_ds.map(tokenize_fn, batched=True)
    val_tokenized = val_ds.map(tokenize_fn, batched=True)
    test_tokenized = test_ds.map(tokenize_fn, batched=True)

    # 5. Initialize Model
    print(f"Initializing Sequence Classification Head for {len(categories)} classes...")
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(categories),
        id2label=id2label,
        label2id=label2id,
    )

    # 6. Training Arguments
    training_args = TrainingArguments(
        output_dir=str(output_dir / "checkpoints"),
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        num_train_epochs=num_epochs,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        logging_steps=10,
        save_total_limit=1,
        report_to="none",
        fp16=torch.cuda.is_available(),
    )

    trainer = WeightedTrainer(
        class_weights=class_weights_tensor,
        model=model,
        args=training_args,
        train_dataset=train_tokenized,
        eval_dataset=val_tokenized,
        processing_class=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        compute_metrics=compute_metrics,
    )

    # 7. Train
    print("Starting training loop...")
    train_result = trainer.train()
    print("Training finished.")

    # 8. Evaluate on Held-out Test Set
    print("\nEvaluating on Held-out Test Set...")
    test_metrics = trainer.evaluate(test_tokenized)
    print(f"Test Set Evaluation Results: {test_metrics}")

    # 9. Save Best Model and Tokenizer
    print(f"\nSaving final model artifact to {output_dir}...")
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    metadata = {
        "model_name": model_name,
        "categories": categories,
        "label2id": label2id,
        "id2label": id2label,
        "train_samples": len(train_df),
        "val_samples": len(val_df),
        "test_samples": len(test_df),
        "test_macro_f1": test_metrics.get("eval_macro_f1", 0.0),
        "test_weighted_f1": test_metrics.get("eval_weighted_f1", 0.0),
        "test_accuracy": test_metrics.get("eval_accuracy", 0.0),
    }

    with open(output_dir / "training_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Metadata saved to {output_dir / 'training_metadata.json'}")
    return metadata


if __name__ == "__main__":
    train_model()
