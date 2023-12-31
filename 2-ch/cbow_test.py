# -*- coding: utf-8 -*-
"""CBOW_test.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/12xugGHbm-12966MOpAX4oxxjKNMiDnLX
"""

from google.colab import drive
drive.mount('/content/drive')

# Commented out IPython magic to ensure Python compatibility.
import sys, os
# %cd /content/drive/MyDrive/Colab Notebooks/밑바닥딥러닝2

from common.util import most_similar, analogy

##CBOW 모델 평가
import pickle

pkl_file = '/content/drive/MyDrive/Colab Notebooks/밑바닥딥러닝2/cbow_params_book.pkl'

with open(pkl_file, 'rb') as f:
    params = pickle.load(f)
    word_vecs = params['word_vecs']
    word_to_id = params['word_to_id']
    id_to_word = params['id_to_word']

querys = ['you', 'year', 'car', 'toyota']
for query in querys:
    most_similar(query, word_to_id, id_to_word, word_vecs, top=5)

##유추문제 풀기
from common.util import most_similar, analogy

# 유추(analogy) 작업
print('-'*50)
analogy('king', 'man', 'queen',  word_to_id, id_to_word, word_vecs)
analogy('take', 'took', 'go',  word_to_id, id_to_word, word_vecs)
analogy('car', 'cars', 'child',  word_to_id, id_to_word, word_vecs)
analogy('good', 'better', 'bad',  word_to_id, id_to_word, word_vecs)