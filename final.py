# coding:utf-8
import tensorflow as tf
import cv2
import numpy as np
import Jetson.GPIO as GPIO
import os
import sys
import jieba
import time
from datetime import datetime
import speech_recognition as sr
import csv

# 修改使用jieba進行斷詞的函數
def cut_words(sentence):
    return jieba.cut(sentence, cut_all=False)

def calc_classification(word_sentence_list):
    ret_cs = []
    ret_le = []
    ret_pa = []
    other = []
    for word in word_sentence_list:
        if word not in stopwords:
            ### eliminate stopsword
            if word in coding_syntax:
                ret_cs.append(word)
            elif word in learning_environment:
                ret_le.append(word)
            elif word in project_assignment:
                ret_pa.append(word)
            else:
                other.append(word)

    return ret_cs , ret_le , ret_pa , other

def get_key(dict, value):
    return [k for k, v in dict.items() if v == value]

# GPIO設定、預設LED關閉、預設聲音關閉
GPIO.setmode(GPIO.BOARD)

led_r = 33
led_g = 21
buzzer = 35

GPIO.setup(led_r, GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(led_g, GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(buzzer, GPIO.OUT, initial = GPIO.LOW)

# 初始化藥物編號與儲存陣列
medicine = {"1":"B群", "2":"葉黃素", "3":"魚油", "4":"鈣片"}
weekend = [[], [], [], [], [], [], []]
B = []
Y = []
F = []
C = []

# Read ontology_words from CSV file
coding_syntax = []
learning_environment = []
project_assignment = []
all_words_for_jieba = []

# 載入模型、資料格式設定、相機抓取
model = tf.keras.models.load_model('keras_model.h5', compile=False)
data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
cap = cv2.VideoCapture(0)

# 進入功能
while(True):
    choice = int(input("功能選項：(1)規劃每天藥品 (2)查看目前藥物規劃 (3)使用 (4)新增藥物 (5)語音詢問 (6)結束 \n"))
    if(choice == 1):
        while(True):
            choice2 = int(input("想要設定星期幾的藥物? \n"))

            # 設定當日藥物並print出來
            print("請輸入藥物編號：(1)B群 (2)葉黃素 (3)魚油 (4)鈣片")
            med = str(input())
            if(med == '1'):
                B.append(choice2)
            elif(med == '2'):
                Y.append(choice2)
            elif(med == '3'):
                F.append(choice2)
            elif(med == '4'):
                C.append(choice2)

            weekend[choice2-1].append(medicine[med])

            # 判斷是否要繼續設定藥物
            choice3 = int(input("功能選擇：(1)繼續設定藥物 (2)結束 \n"))
            if(choice3 == 2):
              print("目前設定好的藥物為：")
              for i in range(len(weekend[choice2-1])):
                print(weekend[choice2-1][i] + "\t")
              break

    elif(choice == 2):
        # 印出目前每天規劃的藥物
        for i in range(len(weekend)):
            print("星期" + str((i + 1)) + ": \t")
            for j in range(len(weekend[i])):
                print(weekend[i][j] + "\t")
            print("\n")

    elif(choice == 3):
        # 判斷今日要吃的藥物
        today_med = []
        today = datetime.today().weekday()
        print("今天星期" + str(today + 1) + "，要吃的藥有： \t")
        for i in range(len(weekend[today])):
            print(weekend[today][i] + "\t")
            med_num = get_key(medicine, weekend[today][i])
            today_med.append(int(med_num[0]))
        answerCount = len(today_med)
        print(answerCount)

        # 判斷相機是否開啟
        if not cap.isOpened():
            print("Cannot open camera")
            exit()

        # 進入辨識畫面
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Cannot receive frame")
                break
            img = cv2.resize(frame , (398, 224))
            img = img[0:224, 80:304]
            image_array = np.asarray(img)
            normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
            data[0] = normalized_image_array
            prediction = model.predict(data)
            a,b,c,d = prediction[0]
            answerCounter = 0

            if a > 0.9:
                answer = 1
                if answer in today_med:
                    print("魚油")
                    GPIO.output(buzzer, GPIO.HIGH)
                    time.sleep(0.5)
                    GPIO.output(buzzer, GPIO.LOW)
                    GPIO.output(led_g, GPIO.HIGH)
                    GPIO.output(led_r, GPIO.LOW)
                    answerCounter += 1
                else:
                    print("不是今日藥物")
                    GPIO.output(buzzer, GPIO.LOW)
                    GPIO.output(led_g, GPIO.LOW)
                    GPIO.output(led_r, GPIO.HIGH)
            if b > 0.9:
                answer = 2
                if answer in today_med:
                    print("葉黃素")
                    GPIO.output(buzzer, GPIO.HIGH)
                    time.sleep(0.5)
                    GPIO.output(buzzer, GPIO.LOW)
                    GPIO.output(led_g, GPIO.HIGH)
                    GPIO.output(led_r, GPIO.LOW)
                    answerCounter += 1
                else:
                    print("不是今日藥物")
                    GPIO.output(buzzer, GPIO.LOW)
                    GPIO.output(led_g, GPIO.LOW)
                    GPIO.output(led_r, GPIO.HIGH)
            if c > 0.9:
                answer = 3
                if answer in today_med:
                    print("B群")
                    GPIO.output(buzzer, GPIO.HIGH)
                    time.sleep(0.5)
                    GPIO.output(buzzer, GPIO.LOW)
                    GPIO.output(led_g, GPIO.HIGH)
                    GPIO.output(led_r, GPIO.LOW)
                    answerCounter += 1
                else:
                    print("不是今日藥物")
                    GPIO.output(buzzer, GPIO.LOW)
                    GPIO.output(led_g, GPIO.LOW)
                    GPIO.output(led_r, GPIO.HIGH)
            if d > 0.9:
                answer = 4
                if answer in today_med:
                    print("鈣片")
                    GPIO.output(buzzer, GPIO.HIGH)
                    time.sleep(0.5)
                    GPIO.output(buzzer, GPIO.LOW)
                    GPIO.output(led_g, GPIO.HIGH)
                    GPIO.output(led_r, GPIO.LOW)
                    answerCounter += 1
                else:
                    print("不是今日藥物")
                    GPIO.output(buzzer, GPIO.LOW)
                    GPIO.output(led_g, GPIO.LOW)
                    GPIO.output(led_r, GPIO.HIGH)

            if answerCounter == answerCount:
                break

            cv2.imshow('藥品辨識畫面', img)
            if cv2.waitKey(500) == ord('q'):
                break

        cv2.destroyAllWindows()

    elif(choice == 4):
        # 設定新增藥物
        while(True):
            print("功能選項：(1)新增藥物 (2)結束")
            choice4 = int(input())
            if(choice4 == 1):
                dict_len = len(medicine)
                medicine[str(dict_len + 1)] = str(input("請輸入藥物名稱："))
            elif(choice4 == 2):
                break

        # 列出所有藥物
        print("目前所有藥物：")
        for i in range(len(medicine)):
            print(str(i+1) + ". " + medicine[str(i+1)] + "\t")

    elif(choice == 5):
        #close system warning
        os.close(sys.stderr.fileno())

        first_row = False
        with open('ontology_words.csv','r',encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            for row in reader:
                if(first_row):
                    if(row[0] != ''):
                        coding_syntax.append(row[0])
                    if(row[1] != ''):
                        learning_environment.append(row[1])
                    if(row[2] != ''):
                        project_assignment.append(row[2])
                if(first_row == False):
                    first_row = True

        # 將 ontology 的詞加入 jieba 的字典
        for word in all_words_for_jieba:
            jieba.add_word(word, freq=100)

        # Read stop words
        stopwords = []
        file = open('stop_word.txt', encoding='utf-8-sig').readlines()
        for lines in file:
            stopwords.append(lines.strip())

        #from IPython.display import clear_output  ##用來清理一下output
        clear_counter = 0
        r = sr.Recognizer()
        while True:
            try:
                with sr.Microphone() as source:
                    print('請開始說話')
                    r.adjust_for_ambient_noise(source)
                    audio = r.listen(source, phrase_time_limit=3)
                    print('開始翻譯.....')
                    text = r.recognize_google(audio, language='zh-TW')  # Convert speech to text using Google recognizer

                    cs, le, pa, ot = calc_classification(list(cut_words(text)))

                    clear_counter += 1
                    if clear_counter == 10:
                        clear_counter = 0
                        os.system('clear')
                    if 'B群' in text:
                        for i in B:
                            print("星期", i, "要吃")
                    if '葉黃素' in text:
                        for i in Y:
                            print("星期", i, "要吃")
                    if '魚油' in text:
                        for i in F:
                            print("星期", i, "要吃")
                    if '鈣片' in text:
                        for i in C:
                            print("星期", i, "要吃")
                    if '退出' in text:
                        break
            except:
                print('Error!')
                clear_counter += 1
                if clear_counter == 10:
                    clear_counter = 0
                    os.system('clear')
        break

cap.release()
GPIO.cleanup()