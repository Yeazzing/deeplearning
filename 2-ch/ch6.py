# -*- coding: utf-8 -*-
"""ch6.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/10K5DxrTUAc3odjLmnpoRAcIdkvGkg1F7
"""

import numpy as np
import matplotlib.pyplot as plt

from google.colab import drive
drive.mount('/content/drive')

# Commented out IPython magic to ensure Python compatibility.
import sys, os
# %cd /content/drive/MyDrive/Colab Notebooks/밑바닥딥러닝2

from common.layers import *
from common.functions import sigmoid

from common.time_layers import *
import pickle

"""RNN의 문제점"""

N = 2  #미니배치 크기
H = 3  #은닉 상태 벡터의 차원 수
T = 20  #시계열 데이터의 길이

dh = np.ones((N, H))
np.random.seed(3)  #재현할 수 있도록 난수의 시드 고정
Wh = np.random.randn(H, H)

norm_list = []
for t in range(T):  #dh 갱신
    dh = np.matmul(dh, Wh.T)
    norm = np.sqrt(np.sum(dh**2)) / N  #미니배치의 평균 L2노름
    norm_list.append(norm)  #각 단계에서 dh크기(노름) 추가

print(norm_list)

# 그래프 그리기
plt.plot(np.arange(len(norm_list)), norm_list)
plt.xticks([0, 4, 9, 14, 19], [1, 5, 10, 15, 20])
plt.xlabel('time step')
plt.ylabel('norm')
plt.show()

N = 2  #미니배치 크기
H = 3  #은닉 상태 벡터의 차원 수
T = 20  #시계열 데이터의 길이

dh = np.ones((N, H))
np.random.seed(3)  #재현할 수 있도록 난수의 시드 고정
#Wh = np.random.randn(H, H) 변경 전
Wh = np.random.randn(H, H) * 0.5  #변경 후

norm_list = []
for t in range(T):  #dh 갱신
    dh = np.matmul(dh, Wh.T)
    norm = np.sqrt(np.sum(dh**2)) / N  #미니배치의 평균 L2노름
    norm_list.append(norm)  #각 단계에서 dh크기(노름) 추가

print(norm_list)

# 그래프 그리기
plt.plot(np.arange(len(norm_list)), norm_list)
plt.xticks([0, 4, 9, 14, 19], [1, 5, 10, 15, 20])
plt.xlabel('time step')
plt.ylabel('norm')
plt.show()

##기울기 클리핑
dW1 = np.random.rand(3,3)*10
dW2 = np.random.rand(3,3)*10
grads = [dW1, dW2]  #기울기의 리스트
max_norm = 5.0  #문턱값

def clip_grads(grads, max_norm):
    total_norm = 0
    for grad in grads:
        total_norm += np.sum(grad**2)
    total_norm = np.sqrt(total_norm)

    rate = max_norm /(total_norm +1e-6)
    if rate <1:
        for grad in grads:
            grad *= rate

"""LSTM 구현"""

class LSTM:
    def __init__(self, Wx, Wh, b):
        self.params = [Wx, Wh, b]  #4개분의 가중치
        self.grads = [np.zeros_like(Wx), np.zeros_like(Wh), np.zeros_like(b)]
        self.cache = None  #순전파 결과 보관했다가 역전파 계산에 사용하려는 용도

    def forward(self, x, h_prev, c_prev):
        Wx, Wh, b = self.params
        N, H = h_prev.shape

        A = np.matmul(x, Wx) +np.matmul(h_prev, Wh) +b  #아핀변환

        #slice
        f = A[:, :H]
        g = A[:, H:2*H]
        i = A[:, 2*H:3*H]
        o = A[:, 3*H:]

        f = sigmoid(f)
        g = np.tanh(g)
        i = sigmoid(i)
        o = sigmoid(o)

        c_next = f*c_prev +g*i
        h_next = o*np.tanh(c_next)

        self.cache = (x, h_prev, c_prev, i, f, g, o, c_next)
        return h_next, c_next

    def backward(self, dh_next, dc_next):
        Wx, Wh, b = self.params
        x, h_prev, c_prev, i, f, g, o, c_next = self.cache

        tanh_c_next = np.tanh(c_next)

        ds = dc_next + (dh_next * o) * (1 - tanh_c_next ** 2)

        dc_prev = ds * f

        di = ds * g
        df = ds * c_prev
        do = dh_next * tanh_c_next
        dg = ds * i

        di *= i * (1 - i)
        df *= f * (1 - f)
        do *= o * (1 - o)
        dg *= (1 - g ** 2)

        dA = np.hstack((df, dg, di, do))  #slice노드의 역전파 처리

        dWh = np.dot(h_prev.T, dA)
        dWx = np.dot(x.T, dA)
        db = dA.sum(axis=0)

        self.grads[0][...] = dWx
        self.grads[1][...] = dWh
        self.grads[2][...] = db

        dx = np.dot(dA, Wx.T)
        dh_prev = np.dot(dA, Wh.T)

        return dx, dh_prev, dc_prev

"""Time LSTM 구현"""

class TimeLSTM:
    def __init__(self, Wx, Wh, b, stateful=False):
        self.params = [Wx, Wh, b]
        self.grads = [np.zeros_like(Wx),np.zeros_like(Wh), np.zeros_like(b)]
        self.layer = None
        self.h, self.c = None, None
        self.dh = None
        self.stateful = stateful

    def forward(self,xs):
        Wx, Wh, b = self.params
        N, T, D = xs.shape
        H = Wh.shape[0]

        self.layers = []
        hs = np.empty((N,T,H), dtype='f')

        if not self.stateful or self.h is None:
            self.h = np.zeros((N, H), dtype='f')
        if not self.stateful or self.c is None:
            self.c = np.zeros((N, H), dtype = 'f')

        for t in range(T):
            layer = LSTM(*self.params)
            self.h, self.c = layer.forward(xs[:, t, :], self.h, self.c)
            hs[:,t, :] = self.h

            self.layers.append(layer)

        return hs

    def backward(self,dhs):
        Wx, Wh, b = self.params
        N, T, H = dhs.shape
        D = Wx.shape[0]

        dxs = np.empty((N, T, D), dtype='f')
        dh, dc = 0,0
        grads = [0,0,0]
        for t in reversed(range(T)):
            layer = self.layers[t]
            dx, dh, dc = layer.backward(dhs[:, t, :]+dh, dc)
            dxs[:, t, :] = dx
            for i , grad in enumerate(layer.grads):
                grads[i] = grad

        for i, grad in enumerate(grads):
            self.grads[i][...] = grad

        self.dh = dh
        return dxs

    def set_state(self, h, c = None):
        self.h, self.c = h, c

    def reset_state(self):
        self.h, self.c = None, None

"""LSTM 언어모델 구현"""

class Rnnlm:
    def __init__(self, vocab_size=10000, wordvec_size=100, hidden_size=100):
        V, D, H = vocab_size, wordvec_size, hidden_size
        rn = np.random.randn

        #가중치 초기화
        embed_W = (rn(V, D)/100).astype('f')
        lstm_Wx = (rn(D, 4*H)/ np.sqrt(D)).astype('f')  #H4개, Xavier초깃값 이용
        lstm_Wh = (rn(H, 4*H)/ np.sqrt(H)).astype('f')
        lstm_b = np.zeros(4*H).astype('f')
        affine_W = (rn(H, V)/ np.sqrt(H)).astype('f')
        affine_b = np.zeros(V).astype('f')

        #계층 생성
        self.layers = [
            TimeEmbedding(embed_W),
            TimeLSTM(lstm_Wx, lstm_Wh, lstm_b, stateful=True),
            TimeAffine(affine_W, affine_b)
        ]
        self.loss_layer = TimeSoftmaxWithLoss()
        self.lstm_layer = self.layers[1]

        #모든 가중치와 기울기를 리스트에 모은다.
        self.params, self.grads = [], []
        for layer in self.layers:
            self.params +=layer.params
            self.grads += layer.grads

    def predict(self, xs):  #문장생성에 사용하기 위해 추가한 메서드
        for layer in self.layers:
            xs = layer.forward(xs)
        return xs

    def forward (self, xs, ts):
        score = self.predict(xs)
        loss = self.loss_layer.forward(score, ts)
        return loss

    def backward (self, dout=1):
        dout = self.loss_layer.backward(dout)
        for layer in reversed(self.layers):
            dout = layer.backward(dout)
        return dout

    def reset_state(self):
        self.lstm_layer.reset_state()

    def save_params(self, file_name = 'Rnnlm.pkl'):  #매개변수 쓰기 처리
        with open(file_name, 'wb') as f:
            pickle.dump(self.params, f)

    def load_params(self, file_name='Rnnlm.pkl'):  #매개변수 읽기 처리
        with open(file_name, 'rb') as f:
            self.params = pickle.load(f)

"""PTB 데이터셋 학습"""

from common.optimizer import SGD
from common.trainer import RnnlmTrainer
from common.util import eval_perplexity
from dataset import ptb

#하이퍼파라미터 설정
batch_size = 20
wordvec_size = 100
hidden_size = 100  #RNN의 은닉 상태 벡터의 원소 수
time_size = 35  #RNN을 펼치는 크기
lr = 20.0
max_epoch = 4
max_grad = 0.25

#학습데이터 읽기
corpus, word_to_id, id_to_word = ptb.load_data('train')
corpus_test, _, _ = ptb.load_data('test')
vocab_size = len(word_to_id)
xs = corpus[:-1]  #입력
ts = corpus[1:]  #출력 (정답 레이블)

#모델 생성
model = Rnnlm(vocab_size, wordvec_size, hidden_size)
optimizer = SGD(lr)
trainer = RnnlmTrainer(model, optimizer)

#1. 기울기 클리핑을 적용하여 학습
trainer.fit(xs, ts, max_epoch, batch_size, time_size, max_grad, eval_interval =20)
#max_grad : 기울기 클리핑 벅용, eval_interval : 20번째 반복마다 퍼플렉서티 평가
trainer.plot(ylim=(0,500))

#2. 테스트 데이터로 평가
model.reset_state()  #모델 상태를 재설정하여 평가 수행
ppl_test = eval_perplexity(model, corpus_test)
print('테스트 퍼플렉서티: ', ppl_test)

#3. 매개변수 저장
model.save_params()  #학습이 완료된 매개변수들을 파일로 저장

"""개선된 RNNLM 구현"""

from common.time_layers import *
from common.np import *
from common.base_model import BaseModel

class BetterRnnlm(BaseModel):
    def __init__(self, vocab_size=10000, wordvec_size=650, hidden_size=650, dropout_ratio = 0.5):
        V, D, H = vocab_size, wordvec_size, hidden_size
        rn = np.random.randn

        #가중치 초기화
        embed_W = (rn(V, D)/100).astype('f')
        lstm_Wx1 = (rn(D, 4*H)/ np.sqrt(D)).astype('f')
        lstm_Wh1 = (rn(H, 4*H)/ np.sqrt(H)).astype('f')
        lstm_b1 = np.zeros(4*H).astype('f')
        lstm_Wx2 = (rn(H, 4*H)/ np.sqrt(H)).astype('f') #lstm계층 2개
        lstm_Wh2 = (rn(H, 4*H)/ np.sqrt(H)).astype('f')
        lstm_b2 = np.zeros(4*H).astype('f')
        affine_b = np.zeros(V).astype('f')


        #계층 생성 #세 가지 개선
        self.layers = [
            TimeEmbedding(embed_W),
            TimeDropout(dropout_ratio),
            TimeLSTM(lstm_Wx1, lstm_Wh1, lstm_b1, stateful=True),
            TimeDropout(dropout_ratio),
            TimeLSTM(lstm_Wx2, lstm_Wh2, lstm_b2, stateful=True),
            TimeDropout(dropout_ratio),
            TimeAffine(embed_W.T, affine_b)  #가중치 공유
        ]
        self.loss_layer = TimeSoftmaxWithLoss()
        self.lstm_layers = [self.layers[2], self.layers[4]]
        self.drop_layers = [self.layers[1], self.layers[3], self.layers[5]]

        #모든 가중치와 기울기를 리스트에 모은다.
        self.params, self.grads = [], []
        for layer in self.layers:
            self.params +=layer.params
            self.grads += layer.grads

    def predict(self, xs, train_flg=False):  #문장생성에 사용하기 위해 추가한 메서드
        for layer in self.drop_layers:
            layer.train_flg = train_flg
        for layer in self.layers:
            xs = layer.forward(xs)
        return xs

    def forward (self, xs, ts, train_flg=True):
        score = self.predict(xs, train_flg)
        loss = self.loss_layer.forward(score, ts)
        return loss

    def backward (self, dout=1):
        dout = self.loss_layer.backward(dout)
        for layer in reversed(self.layers):
            dout = layer.backward(dout)
        return dout

    def reset_state(self):
        for layer in self.lstm_layers:
            layer.reset_state()

"""개선된 모델로 학습 진행"""

from common.optimizer import SGD
from common.trainer import RnnlmTrainer
from common.util import eval_perplexity
from dataset import ptb
from common import config

#하이퍼파라미터 설정
batch_size = 20
wordvec_size = 650
hidden_size = 650  #RNN의 은닉 상태 벡터의 원소 수
time_size = 35  #RNN을 펼치는 크기
lr = 20.0
max_epoch = 4
max_grad = 0.25
dropout = 0.5

#학습데이터 읽기
corpus, word_to_id, id_to_word = ptb.load_data('train')
corpus_val, _, _ = ptb.load_data('val')
corpus_test, _, _ = ptb.load_data('test')
vocab_size = len(word_to_id)
xs = corpus[:-1]  #입력
ts = corpus[1:]  #출력 (정답 레이블)

#모델 생성
model = BetterRnnlm(vocab_size, wordvec_size, hidden_size, dropout)
optimizer = SGD(lr)
trainer = RnnlmTrainer(model, optimizer)

best_ppl = float('inf')
for epoch in range(max_epoch):
    trainer.fit(xs, ts, max_epoch=1, batch_size=batch_size, time_size=time_size, max_grad=max_grad)
    model.reset_state()  #모델 상태를 재설정하여 평가 수행
    ppl = eval_perplexity(model, corpus_val)
    print('검증 퍼플렉서티: ', ppl)  #매 에폭마다 검증 데이터로 퍼플렉서티 평가

    if best_ppl > ppl:
        best_ppl = ppl
        model.save_params()
    else:  #기존퍼플렉서티보다 나빠졌을 경우에만 학습률 낮춤
        lr /=4.0  #학습률 1/4로 줄임
        optimizer.lr = lr

    model.reset_state()
    print('-'*50)

# 테스트 데이터로 평가
model.reset_state()
ppl_test = eval_perplexity(model, corpus_test)
print('테스트 퍼플렉서티: ', ppl_test)