# python run.py \
#     --output_dir=./saved_models \
#     --max_sentnum 150 \
#     --max_wordnum 60 \
#     --patience_step 20 \
#     --do_train \
#     --do_eval \
#     --do_test \
#     --train_data_file=/drive1/cuongtm/BABEL/dataset/PrimeVulBonus/train.jsonl \
#     --eval_data_file=/drive1/cuongtm/BABEL/dataset/PrimeVulBonus/valid.jsonl \
#     --test_data_file=/drive1/cuongtm/vul_fewshot/data/sven/0802.test.jsonl \
#     --epoch 25 \
#     --train_batch_size 84 \
#     --eval_batch_size 64 \
#     --learning_rate 5e-4 \
#     --max_grad_norm 1.0 \
#     --evaluate_during_training \
#     --seed 123456  2>&1 | tee -a train.log

python run.py \
    --output_dir=./saved_models \
    --max_sentnum 150 \
    --max_wordnum 60 \
    --patience_step 20 \
    --do_test \
    --train_data_file=./dataset/Hienlt/primevul_train_raw.jsonl \
    --eval_data_file=./dataset/Hienlt/primevul_val_raw.jsonl \
    --test_data_file=/drive1/cuongtm/BABEL/dataset/PrimeVul/test.jsonl \
    --epoch 10 \
    --train_batch_size 64 \
    --eval_batch_size 64 \
    --learning_rate 5e-4 \
    --max_grad_norm 1.0 \
    --evaluate_during_training \
    --seed 123456  2>&1 | tee -a test_primevul_only.log