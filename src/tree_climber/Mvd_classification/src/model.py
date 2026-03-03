from transformers import AutoModel, AutoTokenizer
import torch.nn as nn

class MVDModel(nn.Module):
    def __init__(self, model_name: str, num_labels: int):
        super(MVDModel, self).__init__()
        self.bert = AutoModel.from_pretrained(model_name)
        self.classifier = nn.Linear(self.bert.config.hidden_size, num_labels)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output
        logits = self.classifier(pooled_output)
        return logits