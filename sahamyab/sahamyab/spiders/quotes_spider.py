import scrapy
import json
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exceptions import DropItem
from scrapy.conf import settings
import psycopg2
import time
import os
import pymongo
import configparser
import sys
from hazm import Normalizer

f=open('myali.json','w',encoding='utf-8')
debu=open('debug.json','w',encoding='utf-8')

# execute below command for collecting comments:
# scrapy crawl sahamyabComments -o data.jl

stock_name = "خساپا"

class SahamyabCommentsSpider(scrapy.Spider):
    name = "sahamyabComments"
    urlTwit = 'https://www.sahamyab.com/app/twiter/list?v=0.1'
    urlLogin = 'https://www.sahamyab.com/api/login'
    urlChangeToken = 'https://www.sahamyab.com/auth/realms/sahamyab/protocol/openid-connect/token'
    baseUrlImage='https://www.sahamyab.com/guest/image/generic/'
    normalizer = Normalizer()
    globalVersion=1
    sahamyabTwitChannelId = -1000
    sahamyabChartChannelId = -2000
    conn=None
    cur=None
    currentPath=os.path.abspath(os.getcwd())
    lastMessageId=-1
    max_try=5
    count_try=0
    accessToken=''
    refreshToken=''
    username = ''
    password = ''
    state = 'twit'

    def createJson(self,id,content,date,senderUsername,senderName,likeCount,parentId,image,version):
        myJson={
            'message':{
                'id': int(id),
                'content': content,
                'date':date,
                'senderUsername': senderUsername,
                'senderName': senderName,
                'likeCount': int(likeCount),
                'parentId': int(parentId),
                'image': image,
                'version': version,
                'read':0,
            }
        }
        #self.writeJsonOpject(myJson)
        #self.writeJsonOpjectToMongo(myJson)

    def updateLastMessageIdToPostgres(self,channelId, lastMessageId):
        debu.write('in updateEmesage , '+str(channelId)+' '+str(lastMessageId))
        self.cur.execute("update channel set lastmessageid=%s where id= %s;",[int(lastMessageId),int(channelId)])
        self.conn.commit()

    def writeJsonOpjectToMongo(self,jsonObject):
        self.collection.insert(jsonObject)
        #self.dbMongo.sahamyab.insert_one(jsonObject)
    
    def init_database(self):
        mhost='localhost'
        mdatabase='telegram'
        muser='postgres'
        mpassword='aliali0321'
        conn = psycopg2.connect(host=mhost,database=mdatabase, user=muser, password=mpassword)
        cur = conn.cursor()
        return conn,cur


    def initUseAndPass(self):
        config = configparser.ConfigParser()
        path=self.currentPath+r'\sahamyabConfig.ini'
        config.read(path)
        self.username=config.get('Sahamyab','username')
        self.password=config.get('Sahamyab','password')
        print(self.username+self.password)

    def writeJsonOpject(self,jsonObject):
        json.dump(jsonObject,f,ensure_ascii=False, indent=4, sort_keys=True, default=str)
        f.flush()

    def addSahamyabChannelToPostgres(self):
        twitId = self.getLastMessageIdFromPostgres(self.sahamyabTwitChannelId)
        chartId = self.getLastMessageIdFromPostgres(self.sahamyabChartChannelId)
        if twitId == -1:
            self.cur.execute("INSERT INTO channel(id,username,name,type,channel_group,lastmessageId) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING id", (self.sahamyabTwitChannelId,'#sahamyab_twit_website','sahamyab twit web','sah',False,0,))
        if chartId == -1:
            self.cur.execute("INSERT INTO channel(id,username,name,type,channel_group,lastmessageId) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING id", (self.sahamyabChartChannelId,'#sahamyab_chart_website','sahamyab chart web','sah',False,0,))
    
    def getLastMessageIdFromPostgres(self,channelId):
        self.cur.execute("SELECT * FROM channel where id=%s" ,[channelId])
        self.conn.commit()
        channelObject=self.cur.fetchall()
        if len(channelObject)>0:
            return channelObject[0][5]
        else:
            return -1
        
    def get_lastMessageId(self,channelId):
        lastMessageId = self.getLastMessageIdFromPostgres(channelId)
        if lastMessageId == -1:
            self.addSahamyabChannelToPostgres()
        return lastMessageId

    def __init__(self):#delay between two consecutive requests
        #self.download_delay = 1.5
        self.state='twit'
        self.conn,self.cur = self.init_database()
        self.addSahamyabChannelToPostgres()
        self.stocks=self.fill_namad()


    def start_requests(self):#first request for collecting comments
        self.initUseAndPass()
        request = scrapy.Request(url=SahamyabCommentsSpider.urlLogin, callback=self.parseLogin, method='GET', body=json.dumps({"username":self.username,"password":self.password,"captchaAnswer":"66577","captchaId":"73ddis2d7b4ghifneioh7e29q6","f":"7b1693f44581b978379ba11a1dd40b4d"})) #
        yield request

    def firstRequstToGetTwit(self,chart):
        headers = {'Authorization' : 'Bearer %s' % self.accessToken}
        if chart :
            requestBody ={ "page": 0,"chart":True,  }
        else:
            requestBody ={ "page": 0,  }
        request = scrapy.Request(url=SahamyabCommentsSpider.urlTwit,headers = headers, callback=self.parse, method='GET', body=json.dumps(requestBody)) #"tag": stock_name
        request.meta['page_number'] = 0
        request.meta['chart']=chart
        return request

    def getNextTwit(self,page_number,last_comment_id,chart):
        headers = {'Authorization' : 'Bearer %s' % self.accessToken}
        if chart :
            requestBody ={"page": page_number, "id": str(last_comment_id),"chart":True }
        else:
            requestBody ={"page": page_number, "id": str(last_comment_id), }
        request = scrapy.Request(url=SahamyabCommentsSpider.urlTwit,headers = headers, callback=self.parse, method='POST', dont_filter=True, body=json.dumps(requestBody))
        request.meta['page_number'] = page_number
        request.meta['last_comment_id'] = last_comment_id
        request.meta['chart']=chart
        return request

    def changeToken(self,pageNumber,lastCommentId):
        form_data = {
            'refresh_token': self.refreshToken,
            'client_id': 'sahamyab',
            'grant_type': 'refresh_token',
            # 'uf': 'RS',
        }
        request = scrapy.FormRequest(url=SahamyabCommentsSpider.urlChangeToken, callback=self.parseChangeToken, method='POST', formdata=form_data)
        request.meta['pageNumber']=pageNumber
        request.meta['lastCommentId']=lastCommentId
        return request
    def fill_namad(self):
        f = open(self.currentPath+r'\name.txt','r',encoding='utf-8')
        namad=f.read()
        f.close()
        return namad.split('\n')

    def parseChangeToken(self,response):
        myresp=json.loads(response.body)
        self.accessToken=myresp['access_token']
        self.refreshToken=myresp['refresh_token']
        #print(response.body)
        yield self.getNextTwit(response.meta['pageNumber'],response.meta['lastCommentId'],response.meta['chart'])

    def parseLogin(self,response):
        myresp=json.loads(response.body)
        self.accessToken=myresp['access_token']
        self.refreshToken=myresp['refresh_token']
        print(response.body)
        yield self.changeState()
        
    def add_person_to_database(self,username,name,type,id):
        self.cur.execute("INSERT INTO person(username,name,type,id) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING" ,(username,name,type,id))
        self.conn.commit()
        return id

    def add_person_channel_to_database(self,personId,channelId):
        self.cur.execute("INSERT INTO person_channel(person_id,channel_id) VALUES (%s,%s) ON CONFLICT DO NOTHING" ,(personId,channelId))
        self.conn.commit()

    def update_image(self,messageId,image):
        self.cur.execute("update message set image=%s where id= %s",(image,messageId))
        self.conn.commit()


    def add_message_to_database(self,id,user_id,channel_id,date,content,stock):
        self.cur.execute("INSERT INTO message(id,user_id,channel_id,date,content,stock) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING" ,(id,user_id,channel_id,date,content,stock,))
        self.conn.commit()

    def parseImage(self, response):
        if response.status != 404:
            responseSplit=response.url.split('/')
            filename = '%s.jpg' % responseSplit[-1]
            #with open(filename, 'wb') as tPhoto:
            #    tPhoto.write(response.body)
            self.update_image(response.meta['messageId'],response.body)
            imagepathUri = self.currentPath+filename
            yield response
        else:
            if(response.meta['requestCount']<5):
                requestImage = scrapy.Request(url=response.url, callback=self.parseImage)
                requestImage.meta['requestCount']=response.meta['requestCount']+1
                yield requestImage

    def changeState(self):
        if self.state =='twit':
            self.lastMessageId = self.get_lastMessageId(self.sahamyabTwitChannelId)
            self.state = 'chart'
            return self.firstRequstToGetTwit(False)
            
        elif self.state == 'chart':
            self.state = 'sleep'
            self.lastMessageId = self.get_lastMessageId(self.sahamyabChartChannelId)
            return self.firstRequstToGetTwit(True)
        elif self.state == 'sleep':
            time.sleep(1)
            self.state = 'twit'
            return self.changeState()# problem and 
        else:
            print('unknown state')
            quit(1)
        
    def check_stock_in_message(self,channelText):
        if(channelText is None):
            return -1
        for index in range(0,len(self.stocks)):
            if( (('#'+self.stocks[index]) in self.normalizer.normalize(channelText))):
                return index
        return -1

    def parse(self, response):
        page_number=0
        last_comment_id=0
        chart_enable = False
        if response.status == 404:
            page_number = response.meta['page_number']
            last_comment_id = response.meta['last_comment_id']
            f.write('\n')
            yield '\n'
        else:
            body = json.loads(response.body)
            page_number = response.meta['page_number']
            chart_enable = response.meta['chart']
            if body['errorCode'] == '0000':
                f.write('meta'+str(response.meta['page_number'])+' '+str(response.meta['chart'])+' \n')
                page_number = response.meta['page_number'] + 1
                last_comment_id = body['items'][9]['id']
                debu.write('pageNumber: '+str(page_number))
                if page_number == 1:
                    channelId = self.sahamyabChartChannelId if response.meta['chart'] else self.sahamyabTwitChannelId
                    debu.write('updataLastMessage in parse'+str(body['items'][0]['id'])+' '+str(channelId))
                    self.updateLastMessageIdToPostgres(channelId,body['items'][0]['id'])
                for onequote in body['items']:
                    if onequote['id'] == self.lastMessageId:
                        yield self.changeState()
                        return
                    index=self.check_stock_in_message(onequote['content'])
                    if  index== -1:
                        continue
                    f.write(str(index)+' -- '+self.stocks[index]+'\n')
                    likeCount= '0'
                    parentId= '0'
                    imageUid = ''
                    flagDownloadImage = False
                    if('likeCount' in onequote):
                        likeCount=onequote['likeCount']
                    if 'parentId' in onequote:
                        parentId = onequote['parentId']
                    if 'imageUid' in onequote:
                        imageUid = onequote['imageUid']
                        flagDownloadImage=True
                    userId='sah_'+onequote['senderUsername']
                    userId= userId if len(userId)<=30 else userId[0:29]
                    channelId = self.sahamyabChartChannelId if response.meta['chart'] else self.sahamyabTwitChannelId
                    self.add_person_to_database(onequote['senderUsername'],onequote['senderName'],'sah',userId)
                    self.add_person_channel_to_database(userId,channelId)
                    self.add_message_to_database(onequote['id'],userId,channelId,onequote['sendTime'],onequote['content'],self.stocks[index])
                    if flagDownloadImage:
                        requestImage=scrapy.Request(url=self.baseUrlImage+imageUid, callback=self.parseImage)
                        requestImage.meta['requestCount']=0
                        requestImage.meta['messageId']=onequote['id']
                        yield requestImage
                f.flush()  
                debu.flush()  
                yield self.getNextTwit(page_number,last_comment_id,chart_enable)
            elif body['errorCode'] == '1006':
                yield self.changeState()
                return
                #yield self.changeToken(response.meta['page_number'],response.meta['last_comment_id'])
            else:
                print('unrecognize error\n')
                yield self.changeState()
                return
        


