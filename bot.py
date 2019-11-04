# -*- coding: utf-8 -*-
import os
import telebot
import time
import random
import threading
from emoji import emojize
from telebot import types
from pymongo import MongoClient
import traceback

token = os.environ['TELEGRAM_TOKEN']
bot = telebot.TeleBot(token)


client=MongoClient(os.environ['database'])
db=client.dnd
users=db.users
nowid = db.nowid
if nowid.find_one({}) == None:
    nowid.insert_one({'id':1})

base = {
    'units':{},
    'alpha_access':False,
    'current_stat':None,
    'current_unit':None
}

classes = ['bard', 'barbarian', 'fighter', 'wizard', 'druid', 'cleric', 'warlock', 'monk', 'paladin',
                  'rogue', 'ranger', 'sorcerer']
        
        
races = ['elf', 'human', 'tiefling', 'half-elf', 'halfling', 'half-orc', 'dwarf', 'gnome']


@bot.message_handler(commands=['create_unit'])
def createunit(m):
    user = createuser(m)
    if not user['alpha_access']:
        bot.send_message(m.chat.id, 'У вас нет альфа-доступа! Пишите @Loshadkin.')
        return
    unit = createunit(user)
    users.update_one({'id':user['id']},{'$set':{'units.'+str(unit['id']):unit}})
    bot.send_message(m.chat.id, 'Вы успешно создали юнита! Теперь настройте его (/set_stats).')
        
      
    
@bot.message_handler(commands=['set_stats'])
def set_stats(m):
    if m.chat.id != m.from_user.id:
        bot.send_message(m.chat.id, 'Можно использовать только в личке!')
        return
    user = createuser(m)
    if not user['alpha_access']:
        bot.send_message(m.chat.id, 'У вас нет альфа-доступа! Пишите @Loshadkin.')
        return
    kbs = []
    kb = types.InlineKeyboardMarkup()
    for ids in user['units']:
        unit = user['units'][ids]
        kbs.append(types.InlineKeyboardButton(text = unit['name'], callback_data = str(unit['id'])+' edit'))
    i = 0
    nextt = False
    toadd=[]
    while i < len(kbs):
        if nextt == True:
            kb.add(*toadd)
            toadd = []
            toadd.append(kbs[i])
            nextt = False
        else:
            toadd.append(kbs[i])
        if i%2 == 1:
            nextt = True
        i+=1
    bot.send_message(m.chat.id, 'Выберите юнита, которого хотите отредактировать.', reply_markup=kb)
        

@bot.message_handler()
def msgs(m):
    user = createuser(m)
    if user['current_stat'] != None and user['current_unit'] != None and m.from_user.id == m.chat.id:
        numbervalues = ['hp', 'maxhp', 'strenght', 'dexterity', 'constitution', 'intelligence', 
                       'wisdom', 'charisma', 'armor_class', 'speed']
        text = False
        if user['current_stat'] in numbervalues:
            test = True
        val = m.text
        if test:
            try:
                val = int(m.text)
            except:
                bot.send_message(m.chat.id, 'Нужно значение типа int!')
                return
        test2 = False    
        if user['current_stat'] == 'race':
            d = races.copy()
            test2 = True
        if user['current_stat'] == 'class':
            d = classes.copy()
            test2 = True
        if test2:
            if m.text.lower() not in d:
                bot.send_message(m.chat.id, 'Такого значения нет в списке существующих!')
                return
        users.update_one({'id':user['id']},{'$set':{'units.'+str(user['current_unit'])+'.'+user['current_stat']:val}})
        bot.send_message(m.chat.id, 'Успешно изменена характеристика "'+user['current_stat']+'" на "'+val+'"!')
        
            
        
        
        
@bot.callback_query_handler(func=lambda call: True)
def inline(call):
    user = createuser(call)
    if 'edit' in call.data:
        unit = user['units'][int(call.data.split(' ')[1])]
        if unit == None:
            bot.answer_callback_query(call.id, 'Такого юнита не существует!', show_alert = True)
            return
        kb = create_edit_kb(unit)
        bot.send_message(m.chat.id, 'Нажмите на характеристику для её изменения.', reply_markup=kb)
        
    elif 'change' in call.data:
        blist = ['inventory', 'spells', 'player', 'photo']
        numbervalues = ['hp', 'maxhp', 'strenght', 'dexterity', 'constitution', 'intelligence', 
                       'wisdom', 'charisma', 'armor_class', 'speed', 'name']
        what = call.data.split(' ')[1]
        unit = user['units'][int(call.data.split(' ')[2])]
        if unit == None:
            bot.answer_callback_query(call.id, 'Такого юнита не существует!', show_alert = True)
            return
        if what not in blist:
            users.update_one({'id':user['id']},{'$set':{'current_unit':unit['id'], 'current_stat':what}})
            if what in numbervalues:
                bot.send_message(m.chat.id, 'Теперь пришлите мне новое значение характеристики "'+what+'".')
            else:
                if what == 'race':
                    r = 'расы'
                    alls = ''
                    for ids in races:
                        alls += '`'+ids+'` '
                elif what == 'class':
                    r = 'классы'
                    alls = ''
                    for ids in classes:
                        alls += '`'+ids+'` '
                bot.send_message(m.chat.id, 'Теперь пришлите мне новое значение характеристики "'+what+'".\n'+
                                 'Существующие '+r+': '+alls, parse_mode = 'markdown')
                
    
    
def create_etit_kb(unit):
    player = users.find_one({'id':unit['player']})
    if player != None:
        player = player['name']+' ('+str(player['id'])+')'
    kb = types.InlineKeyboardMarkup()
    kb.add(addkb(kb, 'Имя: '+unit['name'], 'change name '+str(unit['id'])))
    kb.add(addkb(kb, 'Класс: '+unit['class'], 'change class '+str(unit['id'])))
    kb.add(addkb(kb, 'Раса: '+unit['race'], 'change race '+str(unit['id'])))
    kb.add(addkb(kb, 'Хп: '+str(unit['hp']), 'change hp '+str(unit['id'])))
    kb.add(addkb(kb, 'Макс.хп: '+str(unit['maxhp']), 'change maxhp '+str(unit['id'])))
    kb.add(addkb(kb, 'Сила: '+str(unit['strenght']), 'change strenght '+str(unit['id'])))
    kb.add(addkb(kb, 'Ловкость: '+str(unit['dexterity']), 'change dexterity '+str(unit['id'])))
    kb.add(addkb(kb, 'Телосложение: '+str(unit['constitution']), 'change constitution '+str(unit['id'])))
    kb.add(addkb(kb, 'Интеллект: '+str(unit['intelligence']), 'change intelligence '+str(unit['id'])))
    kb.add(addkb(kb, 'Мудрость: '+str(unit['wisdom']), 'change wisdom '+str(unit['id'])))
    kb.add(addkb(kb, 'Харизма: '+str(unit['charisma']), 'change charisma '+str(unit['id'])))
    kb.add(addkb(kb, 'Класс брони: '+str(unit['armor_class']), 'change armor_class '+str(unit['id'])))
    kb.add(addkb(kb, 'Скорость (в футах): '+str(unit['speed']), 'change speed '+str(unit['id'])))
    kb.add(addkb(kb, 'Инвентарь: '+str(len(unit['inventory']))+' предметов', 'change inventory '+str(unit['id'])))
    kb.add(addkb(kb, 'Заклинания: '+str(len(unit['spells']))+' спеллов', 'change spells '+str(unit['id'])))
    kb.add(addkb(kb, 'Управляющий юнитом: '+str(player)), 'change player '+str(unit['id'])))
    kb.add(addkb(kb, 'Фото', 'change photo '+str(unit['id'])))
    return kb
           
    
    
    
        
def addkb(kb, text, calldata):
        return types.InlineKeyboardButton(text=text, callback_data = calldata)
        
def createunit(user):
    maxx=20
    minn=6
    maxhp = random.randint(8, 20)
    return {
        'id':randomid(),
        'name':randomname(),
        'class':randomclass(),
        'race':randomrace(),
        'hp':maxhp,
        'maxhp':maxhp,
            'strenght':random.randint(minn,maxx),
            'dexterity':random.randint(minn,maxx),
            'constitution':random.randint(minn,maxx),
            'intelligence':random.randint(minn,maxx),
            'wisdom':random.randint(minn,maxx),
            'charisma':random.randint(minn,maxx),
            'armor_class':random.randint(8,16),
        'initiative':10,
        'speed':30,
        'photo':None,
        'death_saves(success)':0,
        'death_saves(fail)':0,
        'spells':{},
        'inventory':{},
        'current_weapon':None,
        'owner':user['id'],
        'player':None
    }
        
  

def randomname():
        names = ['Лурин Нвуд', 'Лонг Лао', 'Корза Ксогоголь', 'Алстон Опплбай', 'Холг', 'Лаэл Бит', 'Иглай Тай', 
                'Унео Ано', 'Джор Нарарис', 'Кара Чернин', 'Хама Ана', 'Мейлиль Думеин', 'Шаумар Илтазяра', 'Ромеро Писакар',
                'Шандри Грэйкасл', 'Зэй Тилататна', 'Силусс Ори', 'Чиаркот Литоари', 'Дикай Талаф', 'Чка Хладоклят', 
                'Вренн']
        return random.choice(names)
        
def randomclass():
        return random.choice(classes)
        
        
def randomrace():
        return random.choice(races)
        

def randomid():
    id = nowid.find_one({})['id']
    nowid.update_one({},{'$inc':{'id':1}})
    return id+1

def createuser(m):
    user = users.find_one({'id':m.from_user.id})
    if user == None:
        users.insert_one(createu(m))
        user = users.find_one({'id':m.from_user.id})
    return user



def createu(m):
    d = {'id':m.from_user.id,
        'name':m.from_user.first_name}
    
    for ids in base:
        d.update({ids:base[ids]})
        
    return d
        

def medit(message_text,chat_id, message_id,reply_markup=None,parse_mode=None):
    return bot.edit_message_text(chat_id=chat_id,message_id=message_id,text=message_text,reply_markup=reply_markup,
                                 parse_mode=parse_mode)   




for ids in users.find({}):
    for idss in base:
        if idss not in ids:
            users.update_one({'id':ids['id']},{'$set':{idss:base[idss]}})

print('7777')
bot.polling(none_stop=True,timeout=600)

