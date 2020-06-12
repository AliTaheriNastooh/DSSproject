from telethon import TelegramClient, events
from telethon import utils
import configparser
from hazm import Normalizer
import psycopg2
import sys
import json
import datetime
import pytz
import os

f=open('output.txt','w',encoding='utf-8')
currentPath=os.path.abspath(os.getcwd())

def writeJsonOpject(jsonObject):
    json.dump(jsonObject,f,ensure_ascii=False, indent=4, sort_keys=True, default=str)
    f.flush()
    f.write(',')
def init_database():
    mhost='localhost'
    mdatabase='telegram'
    muser='postgres'
    mpassword='aliali0321'
    conn = psycopg2.connect(host=mhost,database=mdatabase, user=muser, password=mpassword)
    cur = conn.cursor()
    return conn,cur



def add_person_channel_to_database(personId,channelId):
    myJson={
        'insert':{
            'person_channel':{
                'person_id':personId,
                'channel_id':channelId
            }
        }
    }
    writeJsonOpject(myJson)
    cur.execute("INSERT INTO person_channel(person_id,channel_id) VALUES (%s,%s) ON CONFLICT DO NOTHING" ,(personId,channelId))
    conn.commit()


def add_person_to_database(username,name,type,id):
    if(type=='tel'):
        pass
    elif(type=='sah'):
        id=username
    else:
        print('error in add channel tot database')
        sys.exit('error in add channel tot database')
    myJson={
        'insert':{
            'person':{
                'username':username,
                'name':name,
                'type':type,
                'id':id
            }
        }
    }
    if name!= None:
        name = name[0:29] if len(name)>30 else name
    if username != None:
        username = username[0:29] if len(username)>30 else username
    writeJsonOpject(myJson)
    cur.execute("INSERT INTO person(username,name,type,id) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING" ,(username,name,type,id))
    conn.commit()
    return id


def getLastMessageIdFromPostgres(channelId):
    cur.execute("SELECT * FROM channel where id=%s" ,[channelId])
    conn.commit()
    channelObject=cur.fetchall()
    if len(channelObject)>0:
        return channelObject[0][5]
    else:
        return -1
def add_channel_to_database(id=0,username='none',name='none',type='non',channel_group='non',lastmessageid=-1,new_update='non'):
    if(new_update=='new'):
        myJson={
            'insert':{
                'channel':{
                    'id':id,
                    'username':username,
                    'name':name,
                    'type':type,
                    'channel_group':channel_group,
                    'lastmessageId':lastmessageid
                }
            }
        }   
        cur.execute("INSERT INTO channel(id,username,name,type,channel_group,lastmessageId) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING id", (id,username,name,type,channel_group,lastmessageid,))
    elif(new_update=='update'):
        myJson={
            'update':{
                'channel':{
                    'lastmessageId':lastmessageid
                }
            }
        } 
        cur.execute("UPDATE channel SET lastmessageId = %s",(lastmessageid,))
    else:
        print('error in add channel tot database')
        sys.exit('error in add channel tot database')
    conn.commit()
    writeJsonOpject(myJson)
    return id

def add_message_to_database(user_id,channel_id,date,content,stock,image='non'):
    if(image=='non'):
        myJson={
            'insert':{
                'message':{
                    'user_id':user_id,
                    'channel_id':channel_id,
                    'date':date,
                    'content':content,
                    'stock':stock,
                }
            }
        }  
        cur.execute("INSERT INTO message(user_id,channel_id,date,content,stock) VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING" ,(user_id,channel_id,date,content,stock,))
    else:
        myJson={
            'insert':{
                'message':{
                    'user_id':user_id,
                    'channel_id':channel_id,
                    'date':date,
                    'content':content,
                    'stock':stock,
                    'image': 'has image' if image=='non' else 'hasnt'
                }
            }
        } 
        cur.execute("INSERT INTO message(user_id,channel_id,date,content,stock,image) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING" ,(user_id,channel_id,date,content,stock,image,))
    conn.commit()
    writeJsonOpject(myJson)

async def add_groupMessage(message,stock,channelId,path='non'):
    senderId=message.from_id
    senderPerson = await client.get_entity(senderId)
    if(senderPerson.first_name is None):
        senderPerson.first_name=''
    if(senderPerson.last_name is None):
        senderPerson.last_name=''        
    senderId=add_person_to_database(senderPerson.username,senderPerson.first_name+senderPerson.last_name,'tel',str(senderPerson.id))
    add_person_channel_to_database(senderId,channelId)
    if(path!='non'):
        actualPath=path
        f = open(actualPath,'rb')
        filedata = f.read()
        add_message_to_database(senderId,channelId,message.date,message.text,stock,filedata)
    else:
        add_message_to_database(senderId,channelId,message.date,message.text,stock)



async def add_channelMessage(message,stock,channelUsername,channelId,path='non'):
    username=''
    name=''
    id=''
    if(message.post_author is None):
        username=channelUsername
        name=channelUsername
        id=channelUsername
    else:
        id=message.post_author
        name=message.post_author
        username=channelUsername      
    senderId=add_person_to_database(username,name,'tel',id)
    add_person_channel_to_database(senderId,channelId)
    if(path!='non'):
        actualPath=path
        f = open(actualPath,'rb')
        filedata = f.read()
        add_message_to_database(senderId,channelId,message.date,message.text,stock,filedata)
    else:
        add_message_to_database(senderId,channelId,message.date,message.text,stock)


def check_stock_in_message(channelText):
    if(channelText is None):
        return -1
    for index in range(0,len(stocks)):
        if( (('#'+stocks[index]) in normalizer.normalize(channelText))):
            return index
    return -1


async def addMessage(message,channel_group,channel):
    index=check_stock_in_message(message.text)
    if  index!= -1:
        #print(message)
        path='non'
        if message.photo:
            path = await message.download_media()
        if(channel_group=='false'):
            await add_groupMessage(message,stocks[index],channel.id,path)
        else:
            await add_channelMessage(message,stocks[index],channel.username,channel.id,path)


def get_lastMessageId(channelId):
    lastMessageId = getLastMessageIdFromPostgres(channelId)
    return lastMessageId

def updateLastMessageIdToPostgres(channelId, lastMessageId):
    cur.execute("update channel set lastmessageid=%s where id= %s;",[lastMessageId,channelId])
    conn.commit()

async def updateLastMessage(channel):
    lastMessage = await client.get_messages(channel)
    if len(lastMessage) > 0:
        updateLastMessageIdToPostgres(channel.id, lastMessage[0].id)
    else:
        print('++++zero message+++',channel)

async def check_all_message(channel):
    channel= await client.get_entity(channel)

    lastMessageId = get_lastMessageId(channel.id)
    await updateLastMessage(channel)
    print('lastMessageIdint',lastMessageId)
    if(channel.megagroup==True or channel.broadcast==False):
        channel_group='false'
    else:
        channel_group='true'
    async for message in client.iter_messages(channel):
        if message.date < minDate:
            break
        if message.id == lastMessageId:
            print('---lastMessageId--- ',message.id)
            break
        await addMessage(message,channel_group,channel)


async def getAllMessages(channels):
    for channel in channels:
        await check_all_message(channel)


async def addChannel(name):
    print(name)
    newChannel= await client.get_entity(name)
    #print(newChannel)
    channel_group=''
    if(newChannel.megagroup==True or newChannel.broadcast==False ):
        channel_group='false'
    else:
        channel_group='true'
    channel_id=add_channel_to_database(newChannel.id,name,newChannel.title,'tel',channel_group,0,'new')
    return channel_id
    #me = await client.get_me()
    #print(me.stringify())


async def addChannels(channelList):
    for channel in channelList:
        await addChannel(channel)




def init():
    config = configparser.ConfigParser()
    path=currentPath+r'\teleConfig.ini'
    config.read(path)
    api_id=config.getint('Telegram','api_id')
    api_hash=config['Telegram']['api_hash']
    api_hash = str(api_hash)
    return api_hash,api_id


def fill_namad():
    f = open(currentPath+r'\name.txt','r',encoding='utf-8')
    namad=f.read()
    f.close()
    return namad.split('\n')

def get_channel():
    f = open(currentPath+r'\channel_list.txt','r',encoding='utf-8')
    namad=f.read()
    f.close()
    return namad.split('\n')
async def setEventToGetMessages(channels):
    channelsEntity=[]
    for channel in channels:
        temp=await client.get_entity(channel)
        print(temp.id)
        channelsEntity.append(temp.id)
    @client.on(events.NewMessage())
    async def my_event_handler(event):
        print(event.message.to_id.user_id)
        print(event)

api_hash,api_id=init()
client = TelegramClient('anon', api_id, api_hash)
stocks=fill_namad()
del stocks[-1]
normalizer = Normalizer()
conn,cur=init_database()
channels = get_channel()
min_year=2020
min_month = 6
min_day = 11
minDate = datetime.datetime(min_year,min_month,min_day,tzinfo = pytz.UTC)
f.write('{\n\tqueries:\n\t[\n')
with client:
    client.loop.run_until_complete(addChannels(channels))
    client.loop.run_until_complete(getAllMessages(channels))
    #client.loop.run_until_complete(setEventToGetMessages(channels))
    f.write('\t]\n}')
    f.close()
    #client.run_until_disconnected()
    cur.close()

