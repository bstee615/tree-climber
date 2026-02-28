from __future__ import absolute_import, division, print_function

import re
import argparse
import logging
import os
import random
import json
import torch
import numpy as np
import subprocess
from tqdm import tqdm

from torch.utils.data import DataLoader, Dataset, SequentialSampler, RandomSampler
from torch.utils.data.distributed import DistributedSampler

# from torch.function.tensorboard import SummaryWriter
from sklearn.metrics import precision_score, recall_score, f1_score
from evaluator.clean_gadget import remove_comments, clean_gadget

from model.hierarchical_att_model import HierAttNet

from torch.optim import AdamW

from transformers import (get_linear_schedule_with_warmup,
                          BertConfig, BertForMaskedLM, BertTokenizer,
                          GPT2Config, GPT2LMHeadModel, GPT2Tokenizer,
                          OpenAIGPTConfig, OpenAIGPTLMHeadModel, OpenAIGPTTokenizer,
                          RobertaConfig, RobertaForSequenceClassification, RobertaTokenizer,
                          DistilBertConfig, DistilBertForMaskedLM, DistilBertTokenizer)

logger = logging.getLogger(__name__)

MODEL_CLASSES = {
    'gpt2': (GPT2Config, GPT2LMHeadModel, GPT2Tokenizer),
    'openai-gpt': (OpenAIGPTConfig, OpenAIGPTLMHeadModel, OpenAIGPTTokenizer),
    'bert': (BertConfig, BertForMaskedLM, BertTokenizer),
    'roberta': (RobertaConfig, RobertaForSequenceClassification, RobertaTokenizer),
    'distilbert': (DistilBertConfig, DistilBertForMaskedLM, DistilBertTokenizer)
}
regex = r'^[\s\}\{\)\(,;]*$'


def warn(*args, **kwargs):
    pass


import warnings
import csv

warnings.warn = warn


def set_seed(seed=42):
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    # os.environ['PYHTONHASHSEED'] = str(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def construct_adjacency_matrix(code_list, max_degree):
    text_len = len(code_list)
    matrix = np.eye(text_len).astype('float32')
    # Regular expression pattern to match symbolic names starting with "VAR"
    var_pattern = re.compile(r'\bVAR\d+\b')
    fun_pattern = re.compile(r'\bFUN\d+\b')

    # Mapping to store the index of each symbolic name
    # symbol_index = {}
    for i, start_line in enumerate(code_list):
        # Extract symbolic names using regular expression
        var_start_symbols = var_pattern.findall(start_line)
        fun_start_symbols = fun_pattern.findall(start_line)
        for j in range(i, len(code_list)):
            dst_line = code_list[j]
            var_dst_symbols = var_pattern.findall(dst_line)
            fun_dst_symbols = fun_pattern.findall(dst_line)
            for element in var_dst_symbols:
                if element in var_start_symbols:
                    matrix[i][j] = 1
                    matrix[j][i] = 1
            for element in fun_dst_symbols:
                if element in fun_start_symbols:
                    matrix[i][j] = 1
                    matrix[j][i] = 1
    '''weight for data_matrix'''
    # indegree_list = []
    # outdegree_list = []
    # for row in matrix:
    #     indegree = np.sum(row)
    #     indegree_list.append(indegree)

    # for col in matrix.T:
    #     outdegree = np.sum(col)
    #     outdegree_list.append(outdegree)
    # degree_list = [x + y for x, y in zip(indegree_list, outdegree_list)]

    # centrelity_degree = []
    # for degree in degree_list:
    #     if max_degree > 1:
    #         degree = degree / (max_degree - 1)
    #     else:
    #         degree = 0
    #     centrelity_degree.append(degree)

    # for i in range(matrix.shape[0]):
    #     for j in range(matrix.shape[1]):
    #         if matrix[i][j] == 1:
    #             matrix[i][j] += centrelity_degree[j]

    return matrix




def get_depth_list(code):
    depth_list = []
    for idx, line in enumerate(code):
        if re.match(regex, line):
            depth = -2
        else:
            depth = len(line) - len(line.strip())
        depth = int(depth / 2)
        depth_list.append(depth)
    return depth_list


def connect_elements(depth_list):
    n = len(depth_list)
    connections = np.zeros((n, n))

    def connect(i, j):
        if i < 0 or j >= n or i >= n or j < 0:
            return
        connections[i][j] = 1

    stack = []

    def process_element(index):
        if not stack:
            stack.append(index)
        else:
            while stack and depth_list[stack[-1]] >= depth_list[index]:
                stack.pop()
            if stack:
                connect(stack[-1], index)
            stack.append(index)

    skip_depth = None

    for i in range(n):
        depth = depth_list[i]
        if depth == -1:
            continue
        if depth == 0:
            if stack:
                connect(stack[-1], i)
            stack.append(i)
        else:
            if skip_depth is not None and depth >= skip_depth:
                continue
            process_element(i)
            if depth_list[i] == -1:
                skip_depth = depth

    depth_to_nodes = {}
    for i in range(n):
        depth = depth_list[i]
        if depth == -1:
            continue
        if depth not in depth_to_nodes:
            depth_to_nodes[depth] = []
        depth_to_nodes[depth].append(i)

    for depth_nodes in depth_to_nodes.values():
        for i in range(len(depth_nodes) - 1):
            connect(depth_nodes[i], depth_nodes[i + 1])

    if len(depth_list) > 1:
        connections[0][:] = 0
        connections[0][1] = 1

    return connections


# def add_weight_control(matrix, degree_list):
#     for i in range(matrix.shape[0]):
#         for j in range(matrix.shape[1]):
#             if matrix[i][j] == 1:
#                 matrix[i][j] += degree_list[j]
#     return matrix


def tokenize_sentence(sent, tokenizer):
    # handling extra long sentence, truncate to no more extra max_sentlen
    sent = sent.strip()
    text_tokens = tokenizer.tokenize(sent)
    ids_tokens = tokenizer.convert_tokens_to_ids(text_tokens)
    sent_len = len(text_tokens)
    return text_tokens, ids_tokens, sent_len


def padding_sentence_sequences(index_sequences, max_wordnum, max_sentnum):
    X = np.ones([max_sentnum, max_wordnum], dtype=np.int32)
    if len(index_sequences) > max_sentnum:
        index_sequences = index_sequences[:max_sentnum]
    for i in range(len(index_sequences)):
        sequence_ids = index_sequences[i]
        if len(sequence_ids) > max_wordnum:
            sequence_ids = sequence_ids[:max_wordnum]
        for j in range(len(sequence_ids)):
            word_ids = sequence_ids[j]
            X[i, j] = word_ids
    return X


def pad_and_truncate(sequence, maxlen, dtype='int64', padding='post', truncating='post', value=0):
    x = (np.ones(maxlen) * value).astype(dtype)
    if truncating == 'pre':
        trunc = sequence[-maxlen:]
    else:
        trunc = sequence[:maxlen]
    trunc = np.asarray(trunc, dtype=dtype)
    if padding == 'post':
        x[:len(trunc)] = trunc
    else:
        x[-len(trunc):] = trunc
    return x


def convert_examples_to_features_graph(js, tokenizer, args):
    code_ids = []
    code = js['func']
    format_code = remove_comments(code)
    spliter_code = '\n'.join(line for line in format_code.splitlines() if line.strip())
    new_code = spliter_code.split('\n')
    code_symbolic = clean_gadget(new_code)

    for i, line in enumerate(new_code):
        token_line, ids_line, sentlen = tokenize_sentence(line, tokenizer)
        code_ids.append(ids_line)

    regex = r'^[\s\}\{\)\(,;]*$'
    fliter_code = [line.strip() for line in new_code if not re.match(regex, line)]
    max_degree = len(fliter_code)

    data_matrix = construct_adjacency_matrix(code_symbolic[:args.max_sentnum], max_degree)
    depth_list = get_depth_list(new_code)
    control_matrix = connect_elements(depth_list[:args.max_sentnum])

    data_padding_matrix = np.zeros((args.max_sentnum, args.max_sentnum)).astype('float32')
    control_padding_matrix = np.zeros((args.max_sentnum, args.max_sentnum)).astype('float32')
    data_padding_matrix[:len(data_matrix), :len(data_matrix)] = data_matrix
    control_padding_matrix[:len(control_matrix), :len(control_matrix)] = control_matrix

    attention_mask = [1] * len(code_ids)
    attention_mask = pad_and_truncate(attention_mask, args.max_sentnum)  # 1,100
    source_ids = padding_sentence_sequences(code_ids, args.max_wordnum, args.max_sentnum)

    return InputFeatures_graph(source_ids, attention_mask, 0, js['target'], data_padding_matrix,
                               control_padding_matrix)


class InputFeatures_graph(object):
    """A single training/test features for a example."""

    def __init__(self,
                 input_ids,
                 attention_mask,
                 idx,
                 label,
                 data_matrix,
                 control_matrix
                 ):
        self.input_ids = input_ids
        self.attention_mask = attention_mask
        self.idx = str(idx)
        self.label = label
        self.data_matrix = data_matrix
        self.control_matrix = control_matrix


class TextDataset(Dataset):
    def __init__(self, tokenizer, args, file_path=None, sample_percent=1.):
        self.examples = []
        self.args = args
        total_lines = sum(1 for _ in open(file_path, 'r'))
        with open(file_path) as f:
            for line in tqdm(f, total=total_lines):
                js = json.loads(line.strip())
                self.examples.append(convert_examples_to_features_graph(js, tokenizer, args))

        total_len = len(self.examples)
        num_keep = int(sample_percent * total_len)

        if num_keep < total_len:
            np.random.seed(10)
            np.random.shuffle(self.examples)
            self.examples = self.examples[:num_keep]

        if 'train' in file_path:
            logger.info("*** Total Sample ***")
            logger.info("\tTotal: {}\tselected: {}\tpercent: {}\t".format(total_len, num_keep, sample_percent))
            for idx, example in enumerate(self.examples[:3]):
                logger.info("*** Sample ***")
                logger.info("Total sample".format(idx))
                # logger.info("idx: {}".format(idx))
                # logger.info("label: {}".format(example.label))
                # logger.info("input_tokens: {}".format([x.replace('\u0120','_') for x in example.input_tokens]))
                # logger.info("input_ids: {}".format(' '.join(map(str, example.input_ids))))

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, i):
        return torch.tensor(self.examples[i].input_ids), torch.tensor(
            self.examples[i].attention_mask), torch.tensor(self.examples[i].label), self.examples[i].data_matrix, \
               self.examples[i].control_matrix


def train(args, train_dataset, model, tokenizer):
    """ Train the model """
    args.train_batch_size = args.per_gpu_train_batch_size * max(1, args.n_gpu)
    train_sampler = RandomSampler(train_dataset) if args.local_rank == -1 else DistributedSampler(train_dataset)

    train_dataloader = DataLoader(train_dataset, sampler=train_sampler,
                                  batch_size=args.train_batch_size, num_workers=4, pin_memory=False)
    eval_dataset = TextDataset(tokenizer, args, args.eval_data_file)
    args.max_steps = args.epoch * len(train_dataloader)
    args.save_steps = len(train_dataloader)
    args.warmup_steps = len(train_dataloader)
    args.logging_steps = len(train_dataloader)
    args.num_train_epochs = args.epoch
    model.to(args.device)
    # Prepare optimizer and schedule (linear warmup and decay)
    no_decay = ['bias', 'LayerNorm.weight']
    optimizer_grouped_parameters = [
        {'params': [p for n, p in model.named_parameters() if not any(nd in n for nd in no_decay)],
         'weight_decay': args.weight_decay},
        {'params': [p for n, p in model.named_parameters() if any(nd in n for nd in no_decay)], 'weight_decay': 0.0}
    ]
    optimizer = AdamW(optimizer_grouped_parameters, lr=args.learning_rate, eps=args.adam_epsilon)
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=args.max_steps * 0.1,
                                                num_training_steps=args.max_steps)
    criterion = torch.nn.BCEWithLogitsLoss

    # Train!
    logger.info("***** Running training *****")
    logger.info("  Num examples = %d", len(train_dataset))
    logger.info("  Num Epochs = %d", args.num_train_epochs)
    logger.info("  Instantaneous batch size per GPU = %d", args.per_gpu_train_batch_size)
    logger.info("  Total train batch size (w. parallel, distributed & accumulation) = %d",
                args.train_batch_size * args.gradient_accumulation_steps * (
                    torch.distributed.get_world_size() if args.local_rank != -1 else 1))
    logger.info("  Gradient Accumulation steps = %d", args.gradient_accumulation_steps)
    logger.info("  Total optimization steps = %d", args.max_steps)

    global_step = args.start_step
    tr_loss, logging_loss, avg_loss, tr_nb, tr_num, train_loss = 0.0, 0.0, 0.0, 0, 0, 0
    best_mrr = 0.0
    best_acc = 0.0
    max_val_epoch = 0
    # model.resize_token_embeddings(len(tokenizer))
    model.zero_grad()

    for idx in range(args.start_epoch, int(args.num_train_epochs)):
        # bar = tqdm(train_dataloader,total=len(train_dataloader))
        tr_num = 0
        train_loss = 0
        # for step, batch in enumerate(bar):
        for step, batch in enumerate(train_dataloader):
            inputs = batch[0].to(args.device)
            attention_mask = batch[1].to(args.device)
            labels = batch[2].to(args.device)
            data_matrix = batch[3].to(args.device)
            control_matrix = batch[4].to(args.device)
            model.train()
            loss, logits = model(inputs, attention_mask, labels, data_matrix, control_matrix)

            # lo
            if args.gradient_accumulation_steps > 1:
                loss = loss / args.gradient_accumulation_steps

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), args.max_grad_norm)

            tr_loss += loss.item()
            tr_num += 1
            train_loss += loss.item()
            if avg_loss == 0:
                avg_loss = tr_loss
            avg_loss = round(train_loss / tr_num, 5)

            # bar.set_description("epoch {} loss {}".format(idx, avg_loss))
            # logger.info("epoch {} loss {}".format(idx, avg_loss))

            if (step + 1) % args.gradient_accumulation_steps == 0:
                optimizer.step()
                optimizer.zero_grad()
                scheduler.step()
                global_step += 1
                output_flag = True
                avg_loss = round(np.exp((tr_loss - logging_loss) / (global_step - tr_nb)), 4)
                if args.local_rank in [-1, 0] and args.logging_steps > 0 and global_step % args.logging_steps == 0:
                    logging_loss = tr_loss
                    tr_nb = global_step

                if args.local_rank in [-1, 0] and args.save_steps > 0 and global_step % args.save_steps == 0:

                    if args.local_rank == -1 and args.evaluate_during_training:  # Only evaluate when single GPU otherwise metrics may not average well
                        results = evaluate(args, eval_dataset, model, eval_when_training=True)
                        for key, value in results.items():
                            logger.info("  %s = %s", key, round(value, 4))
                            # Save model checkpoint

                    if results['eval_acc'] > best_acc:
                        max_val_epoch = idx
                        best_acc = results['eval_acc']
                        logger.info("  " + "*" * 20)
                        logger.info("  Best acc:%s", round(best_acc, 4))
                        logger.info("  " + "*" * 20)

                        checkpoint_prefix = 'checkpoint-best-acc'
                        output_dir = os.path.join(args.output_dir, '{}'.format(checkpoint_prefix))
                        if not os.path.exists(output_dir):
                            os.makedirs(output_dir)
                        model_to_save = model.module if hasattr(model, 'module') else model
                        output_dir = os.path.join(output_dir, '{}'.format('model.bin'))
                        torch.save(model_to_save.state_dict(), output_dir)
                        logger.info("Saving model checkpoint to %s", output_dir)
        avg_loss = round(train_loss / tr_num, 5)
        logger.info("epoch {} loss {}".format(idx, avg_loss))
        if idx - max_val_epoch >= args.patience_step:
            print('>> early stop')
            break


def evaluate(args, eval_dataset, model, eval_when_training=False):
    # Loop to handle MNLI double evaluation (matched, mis-matched)
    eval_output_dir = args.output_dir

    if not os.path.exists(eval_output_dir) and args.local_rank in [-1, 0]:
        os.makedirs(eval_output_dir)

    args.eval_batch_size = args.per_gpu_eval_batch_size * max(1, args.n_gpu)
    # Note that DistributedSampler samples randomly
    eval_sampler = SequentialSampler(eval_dataset) if args.local_rank == -1 else DistributedSampler(eval_dataset)
    eval_dataloader = DataLoader(eval_dataset, sampler=eval_sampler, batch_size=args.eval_batch_size, num_workers=4,
                                 pin_memory=False)

    # multi-gpu evaluate
    if args.n_gpu > 1 and eval_when_training is False:
        model = torch.nn.DataParallel(model)

    # Eval!
    logger.info("***** Running evaluation *****")
    logger.info("  Num examples = %d", len(eval_dataset))
    logger.info("  Batch size = %d", args.eval_batch_size)
    eval_loss = 0.0
    nb_eval_steps = 0
    model.eval()
    logits = []
    labels = []
    for batch in eval_dataloader:
        inputs = batch[0].to(args.device)
        attention_mask = batch[1].to(args.device)
        label = batch[2].to(args.device)
        data_matrix = batch[3].to(args.device)
        control_matrix = batch[4].to(args.device)
        with torch.no_grad():
            lm_loss, logit = model(inputs, attention_mask, label, data_matrix, control_matrix)
            eval_loss += lm_loss.mean().item()
            logits.append(logit.cpu().numpy())
            labels.append(label.cpu().numpy())
        nb_eval_steps += 1

    logits = np.concatenate(logits, 0)
    labels = np.concatenate(labels, 0)
    preds = logits[:, 0] > 0.5
    eval_acc = np.mean(labels == preds)
    eval_loss = eval_loss / nb_eval_steps
    perplexity = torch.tensor(eval_loss)

    result = {
        "eval_loss": float(perplexity),
        "eval_acc": round(eval_acc, 4),
    }
    return result


def test(args, model, tokenizer):
    # Loop to handle MNLI double evaluation (matched, mis-matched)
    eval_dataset = TextDataset(tokenizer, args, args.test_data_file)

    args.eval_batch_size = args.per_gpu_eval_batch_size * max(1, args.n_gpu)
    # Note that DistributedSampler samples randomly
    eval_sampler = SequentialSampler(eval_dataset) if args.local_rank == -1 else DistributedSampler(eval_dataset)
    eval_dataloader = DataLoader(eval_dataset, sampler=eval_sampler, batch_size=args.eval_batch_size)

    # multi-gpu evaluate
    if args.n_gpu > 1:
        model = torch.nn.DataParallel(model)

    # Eval!
    
    logger.info("***** Running Test *****")
    logger.info("  Num examples = %d", len(eval_dataset))
    logger.info("  Batch size = %d", args.eval_batch_size)
    eval_loss = 0.0
    nb_eval_steps = 0
    model.eval()
    logits = []
    labels = []
    # for batch in tqdm(eval_dataloader,total=len(eval_dataloader)):
    for batch in eval_dataloader:
        inputs = batch[0].to(args.device)
        attention_mask = batch[1].to(args.device)
        label = batch[2].to(args.device)
        data_matrix = batch[3].to(args.device)
        control_matrix = batch[4].to(args.device)

        with torch.no_grad():
            logit = model(inputs, attention_mask=attention_mask, labels=None, data_matrix=data_matrix,
                          control_matrix=control_matrix)
            # logit = model(inputs, attention_mask, labels, data_matrix, control_matrix)
            logits.append(logit.cpu().numpy())
            labels.append(label.cpu().numpy())

    logits = np.concatenate(logits, 0)
    labels = np.concatenate(labels, 0)
    preds = logits[:, 0] > 0.5

    test_acc = np.mean(labels == preds)
    # test_acc = accuracy_score(labels, preds)
    test_precision = precision_score(labels, preds)
    test_recall = recall_score(labels, preds)
    test_f1_score = f1_score(labels, preds)
    with open(os.path.join(args.output_dir, "predictions.txt"), 'w') as f:
        for example, pred in zip(eval_dataset.examples, preds):
            if pred:
                f.write(example.idx + '\t1\n')
            else:
                f.write(example.idx + '\t0\n')

    result = {
        "test_acc": round(test_acc, 4),
        "test_precision": round(test_precision, 4),
        "test_recall": round(test_recall, 4),
        "test_f1_score": round(test_f1_score, 4)
    }

    # Save predictions and labels to CSV
    csv_path = "./prediction_labels.csv"
    with open(csv_path, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['idx', 'predicted_label', 'actual_label', 'prediction_score'])
        for example, pred, logit, label in zip(eval_dataset.examples, preds, logits[:, 0], labels):
            csv_writer.writerow([example.idx, int(pred), int(label), float(logit)])
    logger.info("Predictions and labels saved to %s", csv_path)
    return result


def main():
    parser = argparse.ArgumentParser()

    ## Required parameters
    parser.add_argument("--max_sentnum", default=400, type=int)
    parser.add_argument("--max_wordnum", default=60, type=int)
    parser.add_argument("--patience_step", default=5, type=int)
    parser.add_argument("--sent_model", default="data_gcn_cat", type=str)
    parser.add_argument("--train_data_file", default="../dataset/train.jsonl", type=str,
                        help="The input training data file (a text file).")
    parser.add_argument("--output_dir", default="./saved_models", type=str,
                        help="The output directory where the model predictions and checkpoints will be written.")
    # Model_parameters
    parser.add_argument("--head_num", default=12, type=int,
                        help="attn head.")
    parser.add_argument("--kernel_size", default=5, type=int,
                        help=".")
    parser.add_argument("--graph_hidden", default=768, type=int,
                        help="hidden size.")
    parser.add_argument("--sentence_hidden", default=768, type=int,
                        help="feature dim size.")
    # parser.add_argument("--output_hidden", default=768, type=int,
    #                     help="feature dim size.")
    parser.add_argument("--attn_hidden", default=256, type=int,
                        help="feature dim size.")
    parser.add_argument("--output_feature", default=768, type=int,
                        help="hidden size.")
    parser.add_argument("--word_hidden", default=768, type=int,
                        help="feature dim size.")
    parser.add_argument("--graph_relation", default=2, type=int,
                        help="num GNN layers.")

    ## Other parameters
    parser.add_argument("--eval_data_file", default="../dataset/valid.jsonl", type=str,
                        help="An optional input evaluation data file to evaluate the perplexity on (a text file).")
    parser.add_argument("--test_data_file", default="../dataset/test.jsonl", type=str,
                        help="An optional input evaluation data file to evaluate the perplexity on (a text file).")

    parser.add_argument("--model_type", default="roberta", type=str,
                        help="The model architecture to be fine-tuned.")
    parser.add_argument("--model_name_or_path", default="microsoft/codebert-base", type=str,
                        help="The model checkpoint for weights initialization.")

    parser.add_argument("--mlm", action='store_true',
                        help="Train with masked-language modeling loss instead of language modeling.")
    parser.add_argument("--mlm_probability", type=float, default=0.15,
                        help="Ratio of tokens to mask for masked language modeling loss")

    parser.add_argument("--config_name", default="roberta", type=str,
                        help="Optional pretrained config name or path if not the same as model_name_or_path")
    parser.add_argument("--tokenizer_name", default="microsoft/codebert-base", type=str,
                        help="Optional pretrained tokenizer name or path if not the same as model_name_or_path")
    parser.add_argument("--cache_dir", default='microsoft/codebert-base', type=str,
                        help="Optional directory to store the pre-trained models downloaded from s3 (instread of the default one)")
    parser.add_argument("--block_size", default=-1, type=int,
                        help="Optional input sequence length after tokenization."
                             "The training dataset will be truncated in block of this size for training."
                             "Default to the model max input length for single sentence inputs (take into account special tokens).")
    parser.add_argument("--do_train", action='store_true',
                        help="Whether to run training.")
    parser.add_argument("--do_eval", action='store_true',
                        help="Whether to run eval on the dev set.")
    parser.add_argument("--do_test", action='store_true',
                        help="Whether to run eval on the dev set.")
    parser.add_argument("--evaluate_during_training", action='store_true',
                        help="Run evaluation during training at each logging step.")
    parser.add_argument("--do_lower_case", action='store_true',
                        help="Set this flag if you are using an uncased model.")

    parser.add_argument("--train_batch_size", default=4, type=int,
                        help="Batch size per GPU/CPU for training.")
    parser.add_argument("--eval_batch_size", default=4, type=int,
                        help="Batch size per GPU/CPU for evaluation.")
    parser.add_argument('--gradient_accumulation_steps', type=int, default=1,
                        help="Number of updates steps to accumulate before performing a backward/update pass.")
    parser.add_argument("--learning_rate", default=5e-5, type=float,
                        help="The initial learning rate for Adam.")
    parser.add_argument("--weight_decay", default=0.0, type=float,
                        help="Weight deay if we apply some.")
    parser.add_argument("--adam_epsilon", default=1e-8, type=float,
                        help="Epsilon for Adam optimizer.")
    parser.add_argument("--max_grad_norm", default=1.0, type=float,
                        help="Max gradient norm.")
    parser.add_argument("--num_train_epochs", default=1.0, type=float,
                        help="Total number of training epochs to perform.")
    parser.add_argument("--max_steps", default=-1, type=int,
                        help="If > 0: set total number of training steps to perform. Override num_train_epochs.")
    parser.add_argument("--warmup_steps", default=0, type=int,
                        help="Linear warmup over warmup_steps.")

    parser.add_argument('--logging_steps', type=int, default=50,
                        help="Log every X updates steps.")
    parser.add_argument('--save_steps', type=int, default=50,
                        help="Save checkpoint every X updates steps.")
    parser.add_argument('--save_total_limit', type=int, default=None,
                        help='Limit the total amount of checkpoints, delete the older checkpoints in the output_dir, does not delete by default')
    parser.add_argument("--eval_all_checkpoints", action='store_true',
                        help="Evaluate all checkpoints starting with the same prefix as model_name_or_path ending and ending with step number")
    parser.add_argument("--no_cuda", action='store_true',
                        help="Avoid using CUDA when available")
    parser.add_argument('--overwrite_output_dir', action='store_true',
                        help="Overwrite the content of the output directory")
    parser.add_argument('--overwrite_cache', action='store_true',
                        help="Overwrite the cached training and evaluation sets")
    parser.add_argument('--seed', type=int, default=42,
                        help="random seed for initialization")
    parser.add_argument('--epoch', type=int, default=42,
                        help="random seed for initialization")

    parser.add_argument("--local_rank", type=int, default=-1,
                        help="For distributed training: local_rank")

    parser.add_argument("--training_percent", default=1., type=float, help="percet of training sample")
    parser.add_argument("--alpha_weight", default=1., type=float, help="percet of training sample")

    args = parser.parse_args()

    # Setup distant debugging if needed

    # Setup CUDA, GPU & distributed training
    if args.local_rank == -1 or args.no_cuda:
        device = torch.device("cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu")
        args.n_gpu = torch.cuda.device_count()
    else:  # Initializes the distributed backend which will take care of sychronizing nodes/GPUs
        torch.cuda.set_device(args.local_rank)
        device = torch.device("cuda", args.local_rank)
        torch.distributed.init_process_group(backend='nccl')
        args.n_gpu = 1
    args.device = device
    args.per_gpu_train_batch_size = args.train_batch_size // max(args.n_gpu, 1)
    args.per_gpu_eval_batch_size = args.eval_batch_size // max(args.n_gpu, 1)
    # Setup logging
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.INFO if args.local_rank in [-1, 0] else logging.WARN)
    logger.warning("Process rank: %s, device: %s, n_gpu: %s, distributed training: %s",
                   args.local_rank, device, args.n_gpu, bool(args.local_rank != -1))

    # Set seed
    set_seed(args.seed)

    # Load pretrained model and tokenizer

    args.start_epoch = 0
    args.start_step = 0

    config_class, model_class, tokenizer_class = MODEL_CLASSES[args.model_type]
    # config = config_class.from_pretrained(args.cache_dir)
    tokenizer = tokenizer_class.from_pretrained(args.cache_dir)
    bert_model = model_class.from_pretrained(args.cache_dir)

    args.block_size = min(args.block_size, tokenizer.max_len_single_sentence)

    embed_table = bert_model.get_input_embeddings().weight.data.cpu().detach().clone().numpy()

    '''model'''
    model = HierAttNet(args, embed_table=embed_table)
    print(model)

    logger.info("Training/evaluation parameters %s", args)
    # Training
    if args.do_train:
        train_dataset = TextDataset(tokenizer, args, args.train_data_file, args.training_percent)
        train(args, train_dataset, model, tokenizer)

    # Evaluation
    results = {}

    if args.do_test and args.local_rank in [-1, 0]:
        checkpoint_prefix = 'checkpoint-best-acc/model.bin'
        output_dir = os.path.join(args.output_dir, '{}'.format(checkpoint_prefix))
        model.load_state_dict(torch.load(output_dir))
        model.to(args.device)
        test_result = test(args, model, tokenizer)

        logger.info("***** Test results *****")
        for key in test_result.keys():
            logger.info("  %s = %s", key, str(round(test_result[key], 4)))

    return results


if __name__ == "__main__":
    main()
