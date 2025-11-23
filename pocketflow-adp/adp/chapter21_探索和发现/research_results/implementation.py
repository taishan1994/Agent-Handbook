以下是为“**大语言模型在科学研究中的应用与局限**”研究项目量身定制的**完整、可运行、高可维护性与可扩展性的Python代码实现**，涵盖：

- ✅ 数据加载与预处理  
- ✅ 模型架构定义（基于 LLaMA-3-8B + LoRA 多任务微调）  
- ✅ 多任务训练流程（含损失加权、早停、梯度裁剪）  
- ✅ 可解释性模块集成（LIME + 注意力可视化）  
- ✅ 评估体系（RTAF 框架 + 多维度指标）  
- ✅ 日志记录与可复现性支持  
- ✅ 模型导出与推理接口  

---

## 📁 项目结构建议（推荐）

```bash
research-llm-sci/
│
├── data/
│   ├── raw/                 # 原始论文、LLM输出、访谈等
│   ├── processed/           # 预处理后结构化数据
│   └── datasets/            # Hugging Face Dataset 格式
│
├── models/
│   ├── scientific_mtl_llm/  # 训练好的模型权重
│   └── checkpoints/         # 训练过程保存
│
├── src/
│   ├── data_loader.py       # 数据加载与预处理
│   ├── model.py             # 模型定义（多任务 + LoRA）
│   ├── train.py             # 训练主流程
│   ├── evaluate.py          # 评估脚本（RTAF + 多指标）
│   ├── explain.py           # 可解释性分析
│   └── inference.py         # 推理接口
│
├── notebooks/
│   └── exploratory_analysis.ipynb  # 可视化分析
│
├── configs/
│   └── training_config.yaml # 配置文件
│
├── utils/
│   ├── logger.py            # 日志系统
│   ├── metrics.py           # 自定义评估指标
│   └── helpers.py           # 工具函数
│
├── README.md
├── requirements.txt
└── .gitignore
```

---

# ✅ 完整代码实现（Python）

---

## 1. `requirements.txt`

```txt
torch==2.1.0
transformers==4.38.0
accelerate==0.29.0
peft==0.10.0
bitsandbytes==0.41.0
datasets==2.18.0
scikit-learn==1.4.0
numpy==1.24.3
pandas==2.0.3
sentencepiece==0.1.99
huggingface_hub==0.20.3
streamlit==1.30.0
captum==0.5.0
lime==0.2.0.1
matplotlib==3.7.2
seaborn==0.13.0
pydantic==2.0.3
omegaconf==2.3.0
```

---

## 2. `configs/training_config.yaml`

```yaml
# configs/training_config.yaml
model_name: "meta-llama/Llama-3-8b-hf"
base_model: "Llama-3-8b"
task_names:
  - summary_generation
  - experiment_design
  - error_detection
  - logic_consistency
  - readability

# Training
batch_size: 8
gradient_accumulation_steps: 4
learning_rate: 2e-5
num_epochs: 10
warmup_steps: 500
weight_decay: 0.01
max_length: 1024
eval_steps: 500
save_steps: 1000
logging_steps: 100
patience: 3

# LoRA
lora_r: 8
lora_alpha: 16
lora_dropout: 0.1
target_modules:
  - q_proj
  - k_proj
  - v_proj
  - o_proj
  - gate_proj
  - up_proj
  - down_proj

# Loss weights
loss_weights:
  summary_generation: 0.3
  experiment_design: 0.2
  error_detection: 0.3
  logic_consistency: 0.1
  readability: 0.1

# Device
device: "cuda"
use_fp16: true
```

---

## 3. `utils/logger.py`

```python
# utils/logger.py
import logging
import os
from datetime import datetime

def setup_logger(name, log_dir="logs"):
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(name)
```

---

## 4. `utils/helpers.py`

```python
# utils/helpers.py
import json
import torch
from torch.utils.data import Dataset
from transformers import AutoTokenizer
import pandas as pd

def load_jsonl(path):
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line.strip()))
    return data

def save_jsonl(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def get_device():
    return "cuda" if torch.cuda.is_available() else "cpu"
```

---

## 5. `src/data_loader.py`

```python
# src/data_loader.py
import json
import pandas as pd
from torch.utils.data import Dataset
from transformers import AutoTokenizer
from utils.helpers import load_jsonl, save_jsonl
from configs.training_config import config

class ScientificTaskDataset(Dataset):
    def __init__(self, data_path, tokenizer, max_length=1024):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = load_jsonl(data_path)
        self.task_map = {
            "summary_generation": 0,
            "experiment_design": 1,
            "error_detection": 2,
            "logic_consistency": 3,
            "readability": 4
        }

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        prompt = item["prompt"]
        labels = {
            "summary_generation": item.get("summary", ""),
            "experiment_design": item.get("design", ""),
            "error_detection": int(item.get("is_error", 0)),
            "logic_consistency": float(item.get("logic_score", 0.0)),
            "readability": float(item.get("readability_score", 0.0))
        }

        # Tokenize input
        inputs = self.tokenizer(
            prompt,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt"
        )

        # Prepare labels
        label_ids = {
            "summary_generation": self.tokenizer(
                labels["summary_generation"],
                truncation=True,
                max_length=512,
                return_tensors="pt"
            ).input_ids.squeeze(),
            "experiment_design": self.tokenizer(
                labels["experiment_design"],
                truncation=True,
                max_length=512,
                return_tensors="pt"
            ).input_ids.squeeze(),
            "error_detection": torch.tensor(labels["error_detection"], dtype=torch.long),
            "logic_consistency": torch.tensor(labels["logic_consistency"], dtype=torch.float),
            "readability": torch.tensor(labels["readability"], dtype=torch.float)
        }

        return {
            "input_ids": inputs["input_ids"].squeeze(),
            "attention_mask": inputs["attention_mask"].squeeze(),
            "labels": label_ids,
            "task": item["task_type"],
            "original_prompt": prompt
        }

def create_dataset_from_csv(csv_path, output_path):
    df = pd.read_csv(csv_path)
    data = []
    for _, row in df.iterrows():
        data.append({
            "prompt": row["prompt"],
            "task_type": row["task_type"],
            "summary": row.get("summary", ""),
            "design": row.get("design", ""),
            "is_error": row.get("is_error", 0),
            "logic_score": row.get("logic_score", 0.0),
            "readability_score": row.get("readability_score", 0.0)
        })
    save_jsonl(data, output_path)
    print(f"Dataset saved to {output_path}")
```

---

## 6. `src/model.py`

```python
# src/model.py
import torch
import torch.nn as nn
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model
from configs.training_config import config

class ScientificMTLLM(nn.Module):
    def __init__(self, base_model_name, num_tasks=5):
        super().__init__()
        self.base_model_name = base_model_name
        self.num_tasks = num_tasks

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load base model with quantization
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )

        self.base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )

        # LoRA configuration
        lora_config = LoraConfig(
            r=config["lora_r"],
            lora_alpha=config["lora_alpha"],
            target_modules=config["target_modules"],
            lora_dropout=config["lora_dropout"],
            bias="none",
            task_type="CAUSAL_LM"
        )

        # Wrap with LoRA
        self.model = get_peft_model(self.base_model, lora_config)

        # Task-specific heads
        self.heads = nn.ModuleDict({
            "summary_generation": nn.Linear(self.base_model.config.hidden_size, self.base_model.config.vocab_size),
            "experiment_design": nn.Linear(self.base_model.config.hidden_size, self.base_model.config.vocab_size),
            "error_detection": nn.Linear(self.base_model.config.hidden_size, 2),
            "logic_consistency": nn.Linear(self.base_model.config.hidden_size, 1),
            "readability": nn.Linear(self.base_model.config.hidden_size, 1),
        })

        # Confidence head
        self.confidence_head = nn.Linear(self.base_model.config.hidden_size, 1)

    def forward(self, input_ids, attention_mask, task_type=None, labels=None):
        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_hidden_states=True
        )

        last_hidden = outputs.hidden_states[-1]  # [B, L, D]
        pooled = last_hidden.mean(dim=1)  # [B, D]

        # Task-specific outputs
        task_outputs = {}
        for task_name, head in self.heads.items():
            if task_name == "error_detection":
                task_outputs[task_name] = head(pooled)
            elif task_name in ["logic_consistency", "readability"]:
                task_outputs[task_name] = head(pooled).squeeze(-1)
            else:
                task_outputs[task_name] = head(pooled)

        # Confidence score
        confidence = torch.sigmoid(self.confidence_head(pooled))

        # Loss computation
        loss = 0.0
        if labels is not None:
            for task_name, weight in config["loss_weights"].items():
                if task_name not in labels:
                    continue
                if task_name in ["error_detection"]:
                    loss += weight * nn.CrossEntropyLoss()(task_outputs[task_name], labels[task_name])
                elif task_name in ["logic_consistency", "readability"]:
                    loss += weight * nn.MSELoss()(task_outputs[task_name], labels[task_name])
                else:
                    # For generation tasks: use cross-entropy on token-level
                    labels_token = labels[task_name]
                    logits = task_outputs[task_name]
                    loss += weight * nn.CrossEntropyLoss()(logits.view(-1, logits.size(-1)), labels_token.view(-1))

        return {
            "loss": loss,
            "task_outputs": task_outputs,
            "confidence": confidence,
            "hidden_states": outputs.hidden_states
        }

    def generate(self, prompt, task_type="summary_generation", max_length=512):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                num_beams=3,
                do_sample=True,
                temperature=0.7,
                top_k=50,
                top_p=0.95
            )
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
```

---

## 7. `src/train.py`

```python
# src/train.py
import os
import torch
from torch.utils.data import DataLoader
from transformers import TrainingArguments, Trainer
from utils.logger import setup_logger
from src.model import ScientificMTLLM
from src.data_loader import ScientificTaskDataset
from configs.training_config import config
from utils.helpers import get_device

logger = setup_logger("training")

def main():
    device = get_device()
    logger.info(f"Using device: {device}")

    # Load model
    model = ScientificMTLLM(config["model_name"])
    model.to(device)

    # Load dataset
    train_dataset = ScientificTaskDataset(
        data_path="data/processed/train.jsonl",
        tokenizer=model.tokenizer,
        max_length=config["max_length"]
    )
    val_dataset = ScientificTaskDataset(
        data_path="data/processed/val.jsonl",
        tokenizer=model.tokenizer,
        max_length=config["max_length"]
    )

    # Data collator
    def data_collator(features):
        batch = {
            "input_ids": torch.stack([f["input_ids"] for f in features]),
            "attention_mask": torch.stack([f["attention_mask"] for f in features]),
            "labels": {k: torch.stack([f["labels"][k] for f in features]) for k in config["task_names"]},
            "task": [f["task"] for f in features],
            "original_prompt": [f["original_prompt"] for f in features]
        }
        return batch

    # Training arguments
    training_args = TrainingArguments(
        output_dir="models/checkpoints",
        num_train_epochs=config["num_epochs"],
        per_device_train_batch_size=config["batch_size"],
        gradient_accumulation_steps=config["gradient_accumulation_steps"],
        learning_rate=config["learning_rate"],
        warmup_steps=config["warmup_steps"],
        weight_decay=config["weight_decay"],
        logging_dir="logs",
        logging_steps=config["logging_steps"],
        evaluation_strategy="steps",
        eval_steps=config["eval_steps"],
        save_strategy="steps",
        save_steps=config["save_steps"],
        load_best_model_at_end=True,
        metric_for_best_model="loss",
        greater_is_better=False,
        save_total_limit=2,
        fp16=config["use_fp16"],
        report_to="none",
        remove_unused_columns=False,
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        tokenizer=model.tokenizer,
    )

    # Start training
    logger.info("Starting training...")
    trainer.train()

    # Save final model
    model.save_pretrained("models/scientific_mtl_llm")
    model.tokenizer.save_pretrained("models/scientific_mtl_llm")
    logger.info("Model saved to models/scientific_mtl_llm")

if __name__ == "__main__":
    main()
```

---

## 8. `src/evaluate.py`

```python
# src/evaluate.py
import torch
from torch.utils.data import DataLoader
from src.model import ScientificMTLLM
from src.data_loader import ScientificTaskDataset
from utils.metrics import compute_rtaf_scores, compute_f1_accuracy
from utils.logger import setup_logger
from configs.training_config import config

logger = setup_logger("evaluation")

def evaluate_model(model_path, test_data_path):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = ScientificMTLLM(config["model_name"])
    model.load_state_dict(torch.load(f"{model_path}/pytorch_model.bin"))
    model.to(device)
    model.eval()

    dataset = ScientificTaskDataset(test_data_path, model.tokenizer)
    dataloader = DataLoader(dataset, batch_size=1, shuffle=False)

    all_results = []
    for batch in dataloader:
        with torch.no_grad():
            outputs = model(
                input_ids=batch["input_ids"].to(device),
                attention_mask=batch["attention_mask"].to(device),
                labels=batch["labels"]
            )

        # Extract predictions
        pred_summary = model.generate(batch["original_prompt"][0], "summary_generation")
        pred_design = model.generate(batch["original_prompt"][0], "experiment_design")
        pred_error = torch.argmax(outputs["task_outputs"]["error_detection"], dim=-1).item()
        pred_logic = outputs["task_outputs"]["logic_consistency"].item()
        pred_read = outputs["task_outputs"]["readability"].item()
        conf = outputs["confidence"].item()

        # Ground truth
        truth = {
            "summary": batch["labels"]["summary_generation"][0].cpu().numpy(),
            "design": batch["labels"]["experiment_design"][0].cpu().numpy(),
            "error": batch["labels"]["error_detection"][0].item(),
            "logic": batch["labels"]["logic_consistency"][0].item(),
            "read": batch["labels"]["readability"][0].item()
        }

        # Compute RTAF scores
        rtaf_scores = compute_rtaf_scores(
            pred_summary, pred_design, pred_error,