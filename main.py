import requests
import telebot
import json
import random
from translate import Translator
from telebot import types
from bs4 import BeautifulSoup as BS
from config import public_marvel_key,hash,bot_token,ts

_apiBase = 'https://gateway.marvel.com:443/v1/public/'
_path = "usersPoints/points.json"
_data = []
_films = []
_tvShows = []
_games = []

bot = telebot.TeleBot(bot_token)

translator = Translator(from_lang="en", to_lang="uk")

def getDataFromJson():
    global _path
    global _data
    with open(_path, 'r') as f:
        _data = json.loads(f.read())



@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('Знайти персонажа')
    item2 = types.KeyboardButton('Список персонажів')
    item3 = types.KeyboardButton('Вгадай персонажа')
    item4 = types.KeyboardButton('Мої Вгадайки)')
    item5 = types.KeyboardButton('Marvel контент')
    item6 = types.KeyboardButton('Help')
    markup.add(item1,item2, item3,item4,item5,item6)
    bot.send_message(message.chat.id , "Вітаю тебе,я Marvel Bot,твій кишеньковий портал у ВЕЛИКИЙ всесвіт Marvel", reply_markup=markup)

@bot.message_handler(content_types=['text'])
def bot_msg(message):
    global _data
    getDataFromJson()
    newUser = 1
    for user in _data:
        if f'{message.chat.id}' in user: newUser = 0
    if newUser == 1:
        userPoints = 1000
        newUser = {f'{message.chat.id}': userPoints}
        _data.append(newUser)
    if message.chat.type == 'private':
        if message.text == 'Знайти персонажа':
            char = bot.send_message(message.chat.id,"Напиши ім'я")
            bot.register_next_step_handler(char, get_char)
        elif message.text == 'Список персонажів': get_chars(message)
        elif message.text == "Вгадай персонажа": get_rndChar(message)
        elif message.text == "Мої Вгадайки)": getUserPoint(message)
        elif message.text == "Marvel контент":
            markup = types.InlineKeyboardMarkup()
            films = types.InlineKeyboardButton(text="Список Фільмів",callback_data="films")
            series = types.InlineKeyboardButton(text="Список Серілів",callback_data="tv-shows")
            games = types.InlineKeyboardButton(text="Список Ігр",callback_data="games")
            markup.add(films,series,games)
            bot.send_message(message.chat.id,text="Marvel контент:",reply_markup=markup)
        elif message.text == "Help":
            msg = ("Пункт 'Знайти персонажа' - напишіть ім'я потрібного персонажа, щоб отримати інформацію про нього"
            "\n\nПункт 'Список персонажів' - повертає список із 5 персонажів(стрілочки повертають новий списко персонажів)"
            "\n\nПункт 'Вгадай персонажа' - гра, де за фотографією треба із 3 персонажів вгадати хто це(за кожну правильну відповідь додається 5 вгадайок, а якщо не вгадали, то мінус 5)"
            "\n\nПункт 'Мої вгадайки' - повертає кількість Ваших Вгадайок"
            "\n\nПункт 'Marvel Контент' - в залежності від обраної контентку, повертає список цього контенту"
            "\n\n Якщо це не допомогло,то зверніться до (автор)")
            bot.send_message(message.chat.id, text=msg)
        else: bot.send_message(message.chat.id, text="Використайте кнопку Help для отримання інформації")







def get_char(message: types.Message):
    global _apiBase
    name = message.text
    try:

        resChar = requests.get(f'{_apiBase}characters?name={name}&ts={ts}&apikey={public_marvel_key}&hash={hash}')
        data = resChar.json()
        charId = data["data"]["results"][0]["id"]
        nameChar = data["data"]["results"][0]["name"]
        descChar = data["data"]["results"][0]["description"]
        thumbnail = f'{data["data"]["results"][0]["thumbnail"]["path"]}.{data["data"]["results"][0]["thumbnail"]["extension"]}'
        comics = get_comics(charId,message)
        if len(descChar) != 0:
            transDes = translator.translate(descChar)
        else:
            transDes = "Опис відсутній"
        markup = types.InlineKeyboardMarkup()
        if comics == "smthGoingWrong":
            markup.add(types.InlineKeyboardButton(text="Коміксів немає"), callback_data="smtn")
        else:
            for i in range(len(comics)):
                markup.add(types.InlineKeyboardButton(text=f'{comics[i]["title"]}', url=comics[i]["url"]))
        btn_wiki_site = types.InlineKeyboardButton(text='wiki персонажу',
                                                   url=data["data"]["results"][0]["urls"][1]["url"])
        markup.add(btn_wiki_site)
        bot.send_photo(message.chat.id,
                             thumbnail,
                             caption=f"Ім'я - {nameChar}\n"
                                      f"Опис - {transDes}",
                             reply_markup=markup)


    except:
        bot.send_message(message.chat.id,text="Помилка,перевірте правильність введення персонажа")



def get_chars(message: types.Message,offset = 250):
    global _apiBase
    try:
        resChars = requests.get(f'{_apiBase}characters?limit=5&offset={offset}&ts={ts}&apikey={public_marvel_key}&hash={hash}')
        data = resChars.json()
        for i in range(5):
            try:
                nameChar = data["data"]["results"][i]["name"]
                descChar = data["data"]["results"][i]["description"]
                if descChar == "":
                    descChar = "Опис відсутній,якщо бажаєте,то знайдіть цього персонажа за допомогою 'Знайти персонажа'"
                thumbnail = f'{data["data"]["results"][i]["thumbnail"]["path"]}.{data["data"]["results"][i]["thumbnail"]["extension"]}'

                markup = types.InlineKeyboardMarkup()
                btn_wiki_site = types.InlineKeyboardButton(text='wiki персонажу',
                                                           url=data["data"]["results"][i]["urls"][1]["url"])
                markup.add(btn_wiki_site)
                if i == 4:
                    back = types.InlineKeyboardButton("<--", callback_data=f"backChars{offset}")
                    next = types.InlineKeyboardButton("-->", callback_data=f"nextChars{offset}")
                    markup.add(back, next)

                bot.send_photo(message.chat.id,
                               thumbnail,
                               caption=f"Ім'я - {nameChar}\n"
                                       f"Опис - {descChar}\n",
                               reply_markup=markup)
            except:
                pass
    except:
        smthGoingWrong(message)


def get_rndChar(message):
    global _apiBase
    global _path
    global _data
    try:
        id = random.randint(1011000, 1011400)
        trueResChar = requests.get(
            f'{_apiBase}characters/{id}?&ts={ts}&apikey={public_marvel_key}&hash={hash}')
        trueData = trueResChar.json()
        trueThumbnail = f'{trueData["data"]["results"][0]["thumbnail"]["path"]}.{trueData["data"]["results"][0]["thumbnail"]["extension"]}'
        imgNotFound = 0
        if trueThumbnail == "http://i.annihil.us/u/prod/marvel/i/mg/b/40/image_not_available.jpg":
            imgNotFound = 1
            get_rndChar(message)
        trueNameChar = trueData["data"]["results"][0]["name"]
        _trueName = trueNameChar
        if imgNotFound == 0:
            #print(f'true = {trueNameChar}')
            id = random.randint(1011000, 1011400)
            fakeResChar1 = requests.get(
                f'{_apiBase}characters/{id}?&ts={ts}&apikey={public_marvel_key}&hash={hash}')
            fakeData1 = fakeResChar1.json()
            fakeNameChar1 = fakeData1["data"]["results"][0]["name"]

            id = random.randint(1011000, 1011400)
            fakeResChar2 = requests.get(
                f'{_apiBase}characters/{id}?&ts={ts}&apikey={public_marvel_key}&hash={hash}')
            fakeData2 = fakeResChar2.json()
            fakeNameChar2 = fakeData2["data"]["results"][0]["name"]

            charsName = [trueNameChar, fakeNameChar1, fakeNameChar2]

            random.shuffle(charsName)

            markup = types.InlineKeyboardMarkup()

            for i in range(0, 3):
                btnValue = "lose"
                if charsName[i] == trueNameChar: btnValue = "win"
                charBtn = types.InlineKeyboardButton(text=charsName[i], callback_data=f'{btnValue}')
                markup.add(charBtn)

            bot.send_photo(message.chat.id,
                           trueThumbnail,
                           caption="Що це за персонаж?",
                           reply_markup=markup)
    except:
        get_rndChar(message)



def get_comics(id,message):
    try:
        resCharComics = requests.get(
            f'{_apiBase}characters/{id}/comics?limit=4&ts={ts}&apikey={public_marvel_key}&hash={hash}')
        data = resCharComics.json()
        countComics = data["data"]["count"]
        comics_list = []
        for i in range(0,countComics):
            comics = {}
            comics["title"] = data["data"]["results"][i]["title"]
            comics["url"] = data["data"]["results"][i]["urls"][0]["url"]
            comics_list.append(comics)
        return comics_list
    except:
        smthGoingWrong(message)
        return "smthGoingWrong"

def getContentFromMarvel(message,type):
    global _films
    global _games
    global _tvShows
    try:
        res = requests.get(f"https://www.marvel.com/{type}")
        html = BS(res.content,'html.parser')
        for el in html.select(".grid-base > .mvl-card--lob"):
            release = ""
            if el.select('.card-body > .card-footer')[0].text == "":release = "Невідомо"
            else: release = el.select('.card-body > .card-footer > .card-footer__secondary-text')[0].text
            content = {
                'title': el.select('.card-body > .card-body__headline')[0].text,
                'url': 'marvel.com' + el.select('.lob__link')[0].get('href'),
                'src': el.select('.lob__link > .card-content-frame > .card-thumb-frame > .img__wrapper > .card-thumb-frame__thumbnail')[0].get('src'),
                'release': release
            }
            if type == "movies": _films.append(content)
            if type == "tv-shows": _tvShows.append(content)
            if type == "games": _games.append(content)
        sendContent(message,0,type)
    except:
        smthGoingWrong(message)

def sendContent(message,offset,type):
    global _films
    global _games
    global _tvShows
    rangeOffset = offset + 5
    url = ""
    endList = 0
    remainder = 0
    if type == "movies":
        url = _films
        if rangeOffset > len(_films):
            remainder = rangeOffset % len(_films)
            rangeOffset = len(_films)
            endList = 1
    if type == "games":
        url = _games
        if rangeOffset > len(_games):
            remainder = rangeOffset % len(_games)
            rangeOffset = len(_games)
            endList = 1
    if type == "tv-shows":
        url = _tvShows
        if rangeOffset > len(_tvShows):
            remainder = rangeOffset % len(_tvShows)
            rangeOffset = len(_tvShows)
            endList = 1
    for i in range(offset,rangeOffset):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="Marvel Wiki",url=url[i]["url"]))
        if i == rangeOffset - 1:
            index = i
            if endList == 1:
                index += remainder
            next = types.InlineKeyboardButton("-->", callback_data=f"{type[:4]}nextContent{index}")
            back = types.InlineKeyboardButton("<--", callback_data=f"{type[:4]}backContent{index}")
            if i != 4 and i != len(url) - 1:  markup.add(back,next)
            elif i == len(url) - 1: markup.add(back)
            else: markup.add(next)
        bot.send_photo(message.chat.id,
                       url[i]["src"],
                       caption=f"{url[i]['title']}\n"
                               f"Дата релізу : {url[i]['release']}",
                       reply_markup=markup)



def victory(message,win):
    global _data
    global _path
    markup = types.InlineKeyboardMarkup()
    btnTrue = types.InlineKeyboardButton("Так", callback_data="Yes")
    btnFalse = types.InlineKeyboardButton("Ні", callback_data="No")

    markup.add(btnTrue, btnFalse)
    text = ""
    num = 0
    if win == "win":
        text = "Вітаю,це вірна відповідь!Може ще одну гру?"
        num = 5
    else:
        text = "Ну нічого,я й сам всіх не пам'ятаю,спробуєш ще раз?"
        num = -5
    for user in _data:
        if f'{message.chat.id}' in user:
            user[f'{message.chat.id}'] += num
            break
    json.dump(_data, open(_path, 'w'))
    bot.send_message(message.chat.id,
                     text=text,
                     reply_markup=markup)
def sayGoodBye(message):
    bot.send_message(message.chat.id,text="Можемо продовжити в будь-який момент")
def getUserPoint(message):
    global _data
    userPoints = 1000
    for user in _data:
        if f'{message.chat.id}' in user:
            userPoints = user[f'{message.chat.id}']
            break
    bot.send_message(message.chat.id,text=f"Кількість Вгадайок = {userPoints}")

def smthGoingWrong(message):
    bot.send_message(message.chat.id, text="Щось пішло не так")

@bot.callback_query_handler(func=lambda call:True)
def listener(call):
    global _path
    global _data
    global _films
    global _games
    global _tvShows
    if call.message:
        if 'nextChars' in call.data:
            get_chars(call.message,int(call.data[9:]) + 5)
        if 'backChars' in call.data:
            get_chars(call.message,int(call.data[9:]) - 5)
        if "nextContent" in call.data:
            if "movi" in call.data:
                sendContent(call.message,int(call.data[15:]) + 1,"movies")
            if "game" in call.data:
                sendContent(call.message,int(call.data[15:]) + 1,"games")
            if "tv-s" in call.data:
                sendContent(call.message,int(call.data[15:]) + 1,"tv-shows")
        if "backContent" in call.data:
            if "movi" in call.data:
                sendContent(call.message,int(call.data[15:]) - 9,"movies")
            if "game" in call.data:
                sendContent(call.message,int(call.data[15:]) - 9,"games")
            if "tv-s" in call.data:
                sendContent(call.message,int(call.data[15:]) - 9,"tv-shows")
        if call.data == "win":
            victory(call.message,"win")
        if call.data == "lose":
            victory(call.message,"lose")
        if call.data == "Yes":
            get_rndChar(call.message)
        if call.data == "No":
            sayGoodBye(call.message)
        if call.data == "films":
            if len(_films) == 0:
                getContentFromMarvel(call.message,"movies")
            else:
                sendContent(call.message,0,"movies")
        if call.data == "games":
            if len(_games) == 0:
                getContentFromMarvel(call.message,"games")
            else:
                sendContent(call.message,0,"games")
        if call.data == "tv-shows":
            if len(_tvShows) == 0:
                getContentFromMarvel(call.message,"tv-shows")
            else:
                sendContent(call.message,0,"tv-shows")


bot.polling(none_stop=True)



