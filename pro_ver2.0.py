import os
import sys
import math
import time
import queue
import pickle
import threading
from peewee import *
import PySimpleGUI as sg
from Txporn import Txporn
from textblob import TextBlob
from collections import Counter
from asyncio import set_event_loop, new_event_loop, get_event_loop, wait, ensure_future

os.chdir(sys._MEIPASS)
INVERTED_INDEX = os.path.join(sys._MEIPASS, r"inverted_index")
FILE_LEN = os.path.join(sys._MEIPASS, r"file_len")
CACHE_DIR = os.path.join(sys._MEIPASS, 'cache')
CACHE_INDEX = os.path.join(sys._MEIPASS, 'cache_index')
SEARCH = os.path.join(sys._MEIPASS, 'search.png')
RETURN = os.path.join(sys._MEIPASS, 'return.png')
PNG0 = os.path.join(sys._MEIPASS, '0.png')
PNG1 = os.path.join(sys._MEIPASS, '1.png')
PNG2 = os.path.join(sys._MEIPASS, '2.png')
PNG3 = os.path.join(sys._MEIPASS, '3.png')
IMG_FONT = os.path.join(sys._MEIPASS, 'TEMPSITC.TTF')
ICON = os.path.join(sys._MEIPASS, 'owl.ico')

# INVERTED_INDEX = os.path.join(os.path.dirname(sys.executable), r"inverted_index")
# FILE_LEN = os.path.join(os.path.dirname(sys.executable), r"file_len")
# CACHE_DIR = os.path.join(os.path.dirname(sys.executable), 'cache')
# CACHE_INDEX = os.path.join(os.path.dirname(sys.executable), 'cache_index')
# SEARCH = os.path.join(os.path.dirname(sys.executable), 'search.png')
# RETURN = os.path.join(os.path.dirname(sys.executable), 'return.png')
# PNG0 = os.path.join(os.path.dirname(sys.executable), '0.png')
# PNG1 = os.path.join(os.path.dirname(sys.executable), '1.png')
# PNG2 = os.path.join(os.path.dirname(sys.executable), '2.png')
# PNG3 = os.path.join(os.path.dirname(sys.executable), '3.png')
# IMG_FONT = os.path.join(os.path.dirname(sys.executable), 'TEMPSITC.TTF')
# ICON = os.path.join(os.path.dirname(sys.executable), 'owl.ico')

token_dic = dict()

file_count = 2661
file_length = dict()

cache_list = list()

gutenberg_db = PostgresqlDatabase('<data base name>', user='<user name>', password='<user password>',
                           host='<host name>', port='<port number>')


class BaseModel(Model):
    """A base model that will use our Postgresql database"""
    class Meta:
        database = gutenberg_db


class Book(BaseModel):
    author = CharField()
    title = TextField()
    context = BlobField()


word = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
half_word = 'ABCDEFGHIJKL'

sg.theme('Reddit')  # Add a touch of color
# All the stuff inside your window.

column0 = [[sg.Text('Illustrative Sentences', key='TITLE', font='Palatino 48', pad=(110, 50)),
            sg.Button(key='RETURN', button_color=(sg.theme_background_color(), sg.theme_background_color()),
                          image_filename=RETURN, image_subsample=10, border_width=0, pad=((20, 0), 20))]]

column1 = [[sg.InputText(key='INPUT', tooltip='input a word', font='Palatino 20',
                         size=(30, 10), pad=((140, 20), (0, 0))),
            sg.Button(key='GO', button_color=(sg.theme_background_color(), sg.theme_background_color()),
                          image_filename=SEARCH, image_subsample=10, border_width=0,
                      pad=(0, 20), bind_return_key=True)]]

column2 = [[sg.Text(f'{half_word}', key='PH1', enable_events=True, font='Palatino 20', size=(None, 2), pad=(0, 10))],
            [sg.Text(f'{half_word}', key='PH2', enable_events=True, font='Palatino 20', size=(None, 2), pad=(0, 10))],
            [sg.Text(f'{half_word}', key='PH3', enable_events=True, font='Palatino 20', size=(None, 2), pad=(0, 10))],
            [sg.Text(f'{half_word}', key='PH4', enable_events=True, font='Palatino 20', size=(None, 2), pad=(0, 10))]]

frame0 = [[sg.Image(PNG0, key='IMG', size=(400, 300), background_color=sg.theme_background_color())]]

column3 = [[sg.Column(column2, key='COL2', background_color=sg.theme_background_color(), pad=(60, 0)),
            sg.Frame('sentence', frame0, key='FRA0', font='Palatino 12', pad=((40, 0), 0))]]

layout = [[sg.Column(column0, key='COL0', background_color=sg.theme_background_color()),
           sg.Text(f'{word}', key='WORD', font='Palatino 36', pad=(100, 20))],
          [sg.Column(column1, key='COL1', background_color=sg.theme_background_color()),
           sg.Column(column3, key='COL3', background_color=sg.theme_background_color())],
          [sg.ProgressBar(10, orientation='h', size=(80, 10), key='PGB', pad=(50, 50), visible=False)]]
# sg.Multiline(key='CONTEXT', background_color=sg.theme_background_color(),
#              size=(50, None), pad=(50, 0))]]

# Create the Window
window = sg.Window('Illustrative Sentences', layout, size=(800, 500), finalize=True, icon=ICON)


def cosine_score(_input) -> dict:
    score = dict()
    query = dict(Counter(_input))
    for item in query:
        if item in token_dic:
            N_df = file_count/len(token_dic[item])
            for doc_id in token_dic[item]:
                W_td = (1 + math.log10(token_dic[item][doc_id])) * math.log10(N_df)
                W_tq = (1 + math.log10(query[item])) * math.log10(N_df)
                if doc_id in score:
                    score[doc_id] += (W_tq * W_td)
                else:
                    score[doc_id] = W_tq * W_td
    for doc_id in score:
        score[doc_id] /= math.sqrt(file_length[doc_id])
    return score


def search_book(word: str) -> list:
    global token_dic, file_length
    with open(INVERTED_INDEX, "rb") as _file:
        token_dic = pickle.loads(_file.read())
    # with open('index.txt', "w+") as _file:
    #     for token in sorted(token_dic.items(), key=lambda x: x):
    #         _file.write(f'{token[0]}, {token[1]}\n')
    with open(FILE_LEN, "rb") as _file:
        file_length = pickle.loads(_file.read())

    result = cosine_score(word)
    book_list = list()
    for doc_id in sorted(result.items(), key=lambda x: x[1])[:10]:
        print(doc_id[0], doc_id[1])
        book_list.append(doc_id[0])
    print(book_list)
    return book_list


def update_phrases(sentence, word, former, latter, phrases):
    if word in sentence.words:
        _phrase = '\\'
        _tags = sentence.tags
        for i, tag in enumerate(_tags):
            if tag[0] == word:
                if i + 1 < len(_tags) and i - 1 >= 0:
                    _phrase = f'{_tags[i-1][0]} {word} {_tags[i+1][0]}'
                elif i + 1 < len(_tags):
                    _phrase = f'{word} {_tags[i+1][0]}'
                elif i - 1 >= 0:
                    _phrase = f'{_tags[i-1][0]} {word}'
                if _phrase != '\\':
                    _phr = TextBlob(_phrase).words
                    if former != '\\' and latter != '\\':
                        if len(_phr) != 3 or _tags[i - 1][1][0] != former[0] and _tags[i + 1][1][0] != latter[0]:
                            _phrase = '\\'
                    elif former != '\\':
                        if _phr[0] == word or _phr[1] == word and _tags[i - 1][1][0] != former[0]:
                            _phrase = '\\'
                    elif latter != '\\':
                        if _phr[-1] == word or _phr[-2] == word and _tags[i + 1][1][0] != latter[0]:
                            _phrase = '\\'
                if _phrase != '\\':
                    break

        if _phrase != '\\':
            if _phrase in phrases and len(phrases[_phrase][0]) > len(sentence):
                phrases[_phrase] = (sentence, phrases[_phrase][1] + 1)
            elif _phrase not in phrases:
                phrases[_phrase] = (sentence, 1)


async def task(loop, function, sentence, word, former, latter, dictionary):
    await loop.run_in_executor(None, function, sentence, word, former, latter, dictionary)


def get_phrase(_input: list) -> list:
    global cache_list, window
    window.Element('PGB').UpdateBar(current_count=0)
    former, word, latter = _input
    # print(former, word, latter)
    timer = 0
    phrases = dict()

    with open(CACHE_INDEX, "rb") as _file:
        cache_list = pickle.loads(_file.read())

    _list = search_book(word)
    window.Element('PGB').UpdateBar(current_count=0, max=len(_list))
    for index, book_id in enumerate(_list):
        if len(phrases) != 0 and min(doc_id[1][1] for doc_id in sorted(phrases.items(), key=lambda y: y[1][1], reverse=True)[:4]) > 1:
            time.sleep(0.05)
            window.Element('PGB').UpdateBar(current_count=index + 1)
            continue
        if book_id not in cache_list:
            cache_size = sum(d.stat().st_size for d in os.scandir(CACHE_DIR) if d.is_file()) / (1024*1024)
            if cache_size > 10:
                try:
                    os.remove(os.path.join(CACHE_DIR, str(cache_list.pop(0))))
                except FileNotFoundError as _:
                    pass
            for book in Book.filter(id=book_id):
                _data = book.context
            with open(os.path.join(CACHE_DIR, str(book_id)), 'wb') as _file:
                _file.write(_data)
            cache_list.append(book_id)

        with open(os.path.join(CACHE_DIR, str(book_id)), "r+", encoding="ISO-8859-1") as _file:
            _data = _file.read()
        blob = TextBlob(_data.lower())

        start_time = time.time()
        set_event_loop(new_event_loop())
        loop = get_event_loop()
        jobs = list()
        for sentence in blob.sentences:
            jobs.append(
                ensure_future(
                    task(loop, update_phrases, sentence, word, former, latter, phrases)
                )
            )
        loop.run_until_complete(wait(jobs))
        loop.close()
        # print(len(phrases))
        timer += (time.time() - start_time)
        window.Element('PGB').UpdateBar(current_count=index + 1)

    print(timer)
    with open(CACHE_INDEX, "wb") as _file:
        pickle.dump(cache_list, _file)
    result = list()
    for doc_id in sorted(phrases.items(), key=lambda y: y[1][1], reverse=True)[:4]:
        print(doc_id[0], doc_id[1][0], doc_id[1][1])
        result.append((doc_id[0], doc_id[1][0]))
    return result


def process_input(inputting: str) -> list:
    result = list()
    count = 0
    blob = TextBlob(inputting)
    for _word in blob.words:
        if '<' + _word + '>' in inputting:
            result.append(_word.upper())
            inputting = inputting.replace('<' + _word + '>', '', 1)
        else:
            if count <= 1:
                result.append(_word)
            count += 1

    print(result)
    former, latter = '\\', '\\'
    if len(result) == 1:
        word = result[0].lower()
    elif len(result) == 2:
        if result[0].isupper() and result[1].islower():
            former = result[0]
            word = result[1]
        elif result[1].isupper() and result[0].islower():
            word = result[0]
            latter = result[1]
        else:
            word = result[0].lower()
    elif len(result) == 3:
        if result[0].isupper() and result[1].islower() and result[2].isupper():
            former = result[0]
            word = result[1]
            latter = result[2]
        else:
            word = result[0].lower()
    else:
        word = result[0].lower()
        for item in result:
            if item.islower():
                word = item
                break
    res = [former, word, latter]
    return res


def long_operation_thread(_input, gui_queue):
    phrase = get_phrase(_input)
    if phrase is None:
        gui_queue.put(1)
    gui_queue.put(phrase)


def main():
    window.Element('RETURN').Update(visible=False)
    window.Element('WORD').Update(visible=False)
    window.Element('COL3').Update(visible=False)
    # window.Element('FRA0').Update(visible=False)
    window.Refresh()
    window.Refresh()

    gui_queue = queue.Queue()

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read(timeout=100)
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
        # print('You entered ', values['INPUT'])
        # print(event)

        if event == 'GO':
            window.Element('PGB').UpdateBar(current_count=0)
            window.Element('PGB').Update(visible=True)
            _word = values['INPUT'].lower()
            _input = process_input(_word)
            try:
                threading.Thread(target=long_operation_thread,
                                 args=(_input, gui_queue,), daemon=True).start()
            except Exception as e:
                print("Error in threading")
        elif event == 'RETURN':
            window.Element('RETURN').Update(visible=False)
            window.Element('WORD').Update(visible=False)
            window.Element('COL3').Update(visible=False)
            # window.Element('FRA0').Update(visible=False)
            window.Element('INPUT').Update(value='')
            window.Element('TITLE').Update(visible=True)
            window.Element('COL1').Update(visible=True)
        elif event == 'PH1':
            # window.Element('COL3').Update(visible=False)
            window.Element('IMG').Update(filename=PNG0)
            # window.Element('COL3').Update(visible=True)
        elif event == 'PH2':
            # window.Element('COL3').Update(visible=False)
            window.Element('IMG').Update(filename=PNG1)
            # window.Element('COL3').Update(visible=True)
        elif event == 'PH3':
            # window.Element('COL3').Update(visible=False)
            window.Element('IMG').Update(filename=PNG2)
            # window.Element('COL3').Update(visible=True)
        elif event == 'PH4':
            # window.Element('COL3').Update(visible=False)
            window.Element('IMG').Update(filename=PNG3)
            # window.Element('COL3').Update(visible=True)
        # window.Element('CONTEXT').Update(value=f'{_data.tobytes().decode("ISO-8859-1")}', visible=True)
        try:
            phrase = gui_queue.get_nowait()  # get_nowait() will get exception when Queue is empty
        except queue.Empty:
            phrase = None  # break from the loop if no more messages are queued up

            # if message received from queue, display the message in the Window
        if phrase is not None:
            if isinstance(phrase, int):
                phrase = None
            window.Element('TITLE').Update(visible=False)
            window.Element('COL1').Update(visible=False)
            window.Element('PGB').Update(visible=False)
            window.Element('RETURN').Update(visible=True)
            window.Element('WORD').Update(value=f"{_word}", visible=True)
            for i in range(1, 5):
                name = 'PH' + str(i)
                if i > len(phrase):
                    window.Element(name).Update(value='<Find Nothing>')
                    Txporn('<Find Nothing>', font=IMG_FONT, output_name=str(i - 1)).convert()
                else:
                    window.Element(name).Update(value=phrase[i - 1][0])
                    Txporn(str(phrase[i - 1][1]).capitalize(), font=IMG_FONT, output_name=str(i - 1)).convert()
            window.Element('IMG').Update(filename=PNG0)
            window.Element('COL3').Update(visible=True)
            # window.Element('FRA0').Update(visible=True)
    window.close()


if not os.path.exists(CACHE_DIR):
    os.mkdir(CACHE_DIR)
if not os.path.exists(CACHE_INDEX):
    cache_index = list()
    with open(CACHE_INDEX, "wb") as _file:
        pickle.dump(cache_index, _file)
main()
