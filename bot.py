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
spells = db.spells
spells.insert_one({})
if 'barbarian' not in spells.find_one({}):
    spells.update_one({},{'$set':{'barbarian':{}, 'bard':{}, 'fighter':{}, 'wizard':{}, 'druid':{}, 
                                 'cleric':{}, 'warlock':{}, 'monk':{}, 'paladin':{}, 'rogue':{}, 'ranger':{},
                                 'sorcerer':{}}})
if nowid.find_one({}) == None:
    nowid.insert_one({'id':1})

base = {
    'units':{},
    'alpha_access':False,
    'current_stat':None,
    'current_unit':None,
    'spells':{}
}

classes = ['bard', 'barbarian', 'fighter', 'wizard', 'druid', 'cleric', 'warlock', 'monk', 'paladin',
                  'rogue', 'ranger', 'sorcerer']
        
        
races = ['elf', 'human', 'tiefling', 'half-elf', 'halfling', 'half-orc', 'dwarf', 'gnome']


# rangee: [дальность_применения, тип_цели]
# duration: 0, если мгновенное
# damage: [3, 6] = 3d6

class Spell(lvl = 0, casttime = 1, rangee = {'distance':30, 'target_type': 'target'}, duration = 1, 
           savethrow = 'dexterity', damage = [3, 6], heal = [0, 0], actions = ['damage']):
    def __init__(self):
        self.lvl = lvl
        self.casttime = casttime   # действия
        self.range = rangee        # футы
        self.duration = duration   # минуты
        self.savethrow = savethrow
        self.damage = damage
        self.heal = heal
        self.actions = actions


@bot.message_handler(commands=['addspell'])
def addspell(m):
    user = createuser(m)
    if not user['alpha_access']:
        bot.send_message(m.chat.id, 'У вас нет альфа-доступа! Пишите @Loshadkin.')
        return
    spell = createspell()
    users.update_one({'id':user['id']},{'$set':{'spells.'+str(spell['id']):spell}})
    bot.send_message(m.chat.id, 'Вы успешно создали заклинание! Теперь настройте его (/set_spell).')
    
        
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
    
    
@bot.message_handler(commands=['set_spell'])
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
    for ids in user['spells']:
        spell = user['spells'][ids]
        kbs.append(types.InlineKeyboardButton(text = spell['name'], callback_data = str(spell['id'])+' spell_manage'))
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
    bot.send_message(m.chat.id, 'Выберите спелл, который хотите отредактировать.', reply_markup=kb)
        

@bot.message_handler(content_types = ['photo'])
def msgsp(m):
    user = createuser(m)
    if user['current_stat'] != None and user['current_unit'] != None and m.from_user.id == m.chat.id:
        unit = user['units'][user['current_unit']]
        if user['current_stat'] == 'photo':
            users.update_one({'id':user['id']},{'$set':{'units.'+str(user['current_unit'])+'.'+user['current_stat']:m.photo[0].file_id}})
            users.update_one({'id':user['id']},{'$set':{'current_stat':None, 'current_unit':None}})
            bot.send_message(m.chat.id, 'Новое фото установлено!')
            
            
        
@bot.message_handler()
def msgs(m):
    user = createuser(m)
    if user['current_stat'] != None and user['current_unit'] != None and m.from_user.id == m.chat.id:
        unit = user['units'][user['current_unit']]
        numbervalues = ['hp', 'maxhp', 'strenght', 'dexterity', 'constitution', 'intelligence', 
                       'wisdom', 'charisma', 'armor_class', 'speed']
        blist = ['inventory', 'spells', 'player', 'photo']
        if user['current_stat'] not in blist:
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
            users.update_one({'id':user['id']},{'$set':{'units.'+str(user['current_unit'])+'.'+user['current_stat']:val}})
            users.update_one({'id':user['id']},{'$set':{'current_stat':None, 'current_unit':None}})
            bot.send_message(m.chat.id, unit['name']+': успешно изменена характеристика "'+user['current_stat']+'" на "'+val+'"!')
            
        else:
            if user['current_stat'] == 'inventory':
                inv = []
                t = m.text.split(', ')
                for ids in t:
                    inv.append(ids)
                tt = ''
                for ids in inv:
                    tt +=ids+', '
                tt = tt[:len(tt)-2]
                users.update_one({'id':user['id']},{'$set':{'units.'+str(user['current_unit'])+'.'+user['current_stat']: inv}})
                users.update_one({'id':user['id']},{'$set':{'current_stat':None, 'current_unit':None}})
                bot.send_message(m.chat.id, unit['name']+': инвентарь юнита успешно изменён на '+tt+'!')
                
                
                
            ##########################################################
           
            
        
        
        
@bot.callback_query_handler(func=lambda call: True)
def inline(call):
    user = createuser(call)
    if 'edit' in call.data:
        unit = user['units'][int(call.data.split(' ')[0])]
        if unit == None:
            bot.answer_callback_query(call.id, 'Такого юнита не существует!', show_alert = True)
            return
        kb = create_edit_kb(unit)
        bot.send_message(m.chat.id, 'Нажмите на характеристику для её изменения.', reply_markup=kb)
        
    elif 'change' in call.data and 'spell' not in call.data:
        blist = ['inventory', 'spells', 'player', 'photo']
        numbervalues = ['hp', 'maxhp', 'strenght', 'dexterity', 'constitution', 'intelligence', 
                       'wisdom', 'charisma', 'armor_class', 'speed', 'name']
        what = call.data.split(' ')[1]
        unit = user['units'][int(call.data.split(' ')[2])]
        if unit == None:
            bot.answer_callback_query(call.id, 'Такого юнита не существует!', show_alert = True)
            return
        users.update_one({'id':user['id']},{'$set':{'current_unit':unit['id'], 'current_stat':what}})
        if what not in blist:
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
        else:
            if what == 'inventory':
                inv = '`'
                for ids in unit['inventory']:
                    inv += ids+', '
                inv = inv[:len(inv)-2]
                inv += '`'
                bot.send_message(m.chat.id, 'Теперь пришлите мне новый инвентарь, перечисляя предметы через запятую. Текущий '+
                                 'инвентарь: '+inv, parse_mode='markdown')
            elif what == 'photo':
                if unit['photo'] != None:
                    bot.send_photo(m.chat.id, unit['photo'], caption = 'Текущая фотография юнита. Для изменения отправьте новое фото.')
                else:
                    bot.send_message(m.chat.id, 'Фотография отсутствует. Для изменения отправьте новое фото.')
            ################################################
    elif 'spell_manage' in call.data:
        spell = user['spells'][int(call.data.split(' ')[0])]
        if spell == None:
            bot.answer_callback_query(call.id, 'Такого спелла не существует!', show_alert = True)
            return
        kb = create_spell_kb(spell)
        bot.send_message(m.chat.id, 'Нажмите на характеристику для её изменения.', reply_markup=kb)
        
        
                
                
    
def create_spell_kb(spell):
    kb = types.InlineKeyboardMarkup()
    kb.add(addkb(kb, 'Название: '+spell['name'], 'spell_change name '+str(spell['id'])))
    kb.add(addkb(kb, 'Классы: '+str(spell['classes']), 'spell_change classes '+str(spell['id'])))
    kb.add(addkb(kb, 'Описание: '+str(spell['description']), 'spell_change description '+str(spell['id'])))
    kb.add(addkb(kb, 'Уровень: '+str(spell['lvl']), 'spell_change lvl '+str(spell['id'])))
    kb.add(addkb(kb, 'Время каста: '+str(spell['casttime'])+' действий', 'spell_change casttime '+str(spell['id'])))
    kb.add(addkb(kb, 'Дальность применения: '+str(len(spell['range']))+' параметров', 'spell_change range '+str(spell['id'])))
    kb.add(addkb(kb, 'Длительность: '+str(spell['duration']), 'spell_change range '+str(spell['id'])))
    kb.add(addkb(kb, 'Спасбросок: '+str(spell['savethrow']), 'spell_change savethrow '+str(spell['id'])))
    kb.add(addkb(kb, 'Урон: '+str(spell['damage'][0])+'d'+str(spell['damage'][1]), 'spell_change damage '+str(spell['id'])))
    kb.add(addkb(kb, 'Лечение: '+str(spell['heal'][0])+'d'+str(spell['heal'][1]), 'spell_change heal '+str(spell['id'])))
    kb.add(addkb(kb, 'Эффекты спелла: '+str(len(spell['actions'])+' эффектов', 'spell_change actions '+str(spell['id'])))
    return kb
    
    
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
    kb.add(addkb(kb, 'Фото', 'change photo '+str(unit['id'])))
    return kb
           
    
    
def createspell():
    id=randomid()
    return {
        'id':id,
        'name':str(id),
        'classes':['sorcerer', 'wizard'],
        'description':'Описание спелла',
        'lvl':0,
        'casttime':1,
        'range':{'distance':30, 'target_type': 'target'},
        'duration':1,
        'savethrow':'dexterity',
        'damage':[3, 6],
        'heal':[0, 0],
        'actions':['damage']
    }
    
    
        
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
        'inventory':[],
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

