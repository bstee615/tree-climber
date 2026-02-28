import torch
import torch.nn as nn
import math
import numpy as np


class BertSelfAttention_confusion(nn.Module):
    def __init__(self, sentence_hidden, graph_hidden, num_attention_heads, attention_probs_dropout_prob=0.1):
        super(BertSelfAttention_confusion, self).__init__()
        if graph_hidden % num_attention_heads != 0:
            raise ValueError(
                "The hidden size (%d) is not a multiple of the number of attention "
                "heads (%d)" % (graph_hidden, num_attention_heads))
        self.num_attention_heads = num_attention_heads
        self.attention_head_size = int(graph_hidden / num_attention_heads)
        self.all_head_size = self.num_attention_heads * self.attention_head_size

        self.query = nn.Linear(sentence_hidden, self.all_head_size)
        self.key = nn.Linear(graph_hidden, self.all_head_size)
        self.value = nn.Linear(graph_hidden, self.all_head_size)
        # is there any problems if the hidden_size different?
        self.dropout = nn.Dropout(attention_probs_dropout_prob)

    def transpose_for_scores(self, x):
        new_x_shape = x.size()[:-1] + (self.num_attention_heads, self.attention_head_size)
        x = x.view(*new_x_shape)
        return x.permute(0, 2, 1, 3)

    def forward(self, graph_hidden, text_hidden, attention_mask):
        # shape: seq_num * batch_size * hidden_size

        # hidden_states = hidden_states.permute(1,0,2)
        # hidden_states bz,100,256
        # attention_mask bz,100
        extended_attention_mask = attention_mask.unsqueeze(1).unsqueeze(2)  # bz,1,1,100
        attention_mask = (1.0 - extended_attention_mask) * -10000.0  # [1,1,1,1,1,0,0] [0,0,0,0,0,-10000,-10000]
        # print(attention_mask.size())
        # input()
        mixed_query_layer = self.query(text_hidden)
        mixed_key_layer = self.key(graph_hidden)
        mixed_value_layer = self.value(graph_hidden)

        query_layer = self.transpose_for_scores(mixed_query_layer)
        key_layer = self.transpose_for_scores(mixed_key_layer)
        value_layer = self.transpose_for_scores(mixed_value_layer)

        # Take the dot product between "query" and "key" to get the raw attention scores.
        attention_scores = torch.matmul(query_layer, key_layer.transpose(-1, -2))
        attention_scores = attention_scores / math.sqrt(self.attention_head_size)
        # Apply the attention mask is (precomputed for all layers in BertModel forward() function)
        attention_scores = attention_scores + attention_mask  # bz,heads,100,100  bz,1,1,100

        # Normalize the attention scores to probabilities.
        attention_probs = nn.Softmax(dim=-1)(attention_scores)

        # This is actually dropping out entire tokens to attend to, which might
        # seem a bit unusual, but is taken from the original Transformer paper.
        attention_probs = self.dropout(attention_probs)

        context_layer = torch.matmul(attention_probs, value_layer)
        context_layer = context_layer.permute(0, 2, 1, 3).contiguous()
        new_context_layer_shape = context_layer.size()[:-2] + (self.all_head_size,)
        context_layer = context_layer.view(*new_context_layer_shape)

        return context_layer
