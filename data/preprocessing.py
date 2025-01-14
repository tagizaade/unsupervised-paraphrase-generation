import argparse
import csv
import random

from nltk.corpus import stopwords
from nltk.tokenize.treebank import TreebankWordTokenizer
from nltk.tokenize.treebank import TreebankWordDetokenizer
from transformers import AutoTokenizer

from eda import synonym_replacement

arabic_stopwords = [l.strip() for l in open('arabic_synonyms.txt', encoding='utf-8').readlines()]

tokenizer = TreebankWordTokenizer()
detokenizer = TreebankWordDetokenizer()


def remove_stopwords(sentence):
    sentence = tokenizer.tokenize(sentence)
    sentence = [word for word in sentence if word.lower() not in arabic_stopwords]
    sentence = ' '.join(sentence)
    sentence = sentence.replace("''", '"').replace('``', '"')
    sentence = detokenizer.detokenize(sentence.split())
    return sentence


def sentence_noising(sentence, shuffle_ratio=0.2, replace_ratio=0.2):
    # 1. Synonym replacement
    words = sentence.split()
    n_sr = max(1, int(len(words)*shuffle_ratio))
    words = synonym_replacement(words, n_sr)

    # 2. Random shuffling
    if random.random() < shuffle_ratio:
        random.shuffle(words)

    return ' '.join(words)


def data_preparation(args):
    gpt_tokenizer = AutoTokenizer.from_pretrained('aubmindlab/aragpt2-base')
    data = []
    with open(args.input, encoding='utf-8') as f:
        skipped = 0
        for line in f:
            sentence = line.strip()
            corrupted_sentence = remove_stopwords(sentence)
            write_line = corrupted_sentence + '\n' + sentence
            if len(gpt_tokenizer.encode(write_line)) < args.max_length:
                data.append([corrupted_sentence, sentence])
            else:
                skipped += 1
    print("Skipped: {}".format(skipped))

    with open(args.output, 'w', encoding='utf-8') as wf:
        writer = csv.writer(wf)
        for corrupted, sentence in data:
            writer.writerow([corrupted, sentence])

    if args.save_noised_output is True:
        with open(args.noised_output, 'w') as wf:
            writer = csv.writer(wf)
            for corrupted, sentence in data:
                corrupted = sentence_noising(corrupted)
                writer.writerow([corrupted, sentence])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, required=True,
                        help='input file')
    parser.add_argument('--output', type=str, required=True,
                        help='output sentence after removing stop words')

    parser.add_argument('--save_noised_output', action="store_true",
                        help='add noise: synonym replacement and shuffling')
    parser.add_argument('--noised_output', type=str, default=None,
                        help='output sentences with additional noise')

    parser.add_argument('--max_length', type=int, default=1024)
    parser.add_argument('--seed', type=int, default=1234)

    args = parser.parse_args()

    random.seed(args.seed)

    if args.noised_output is None:
        args.noised_output = args.output + '.0'

    data_preparation(args)
