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
    'alpha_access':False
}


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

