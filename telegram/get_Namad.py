from lxml import etree
from hazm import Normalizer
import urllib.request
import requests
f = open(r'E:\job\bourse\v1_code\name.txt','w',encoding='utf-8')
normalizer = Normalizer()
#f.write('سلام')
#print(f.read())
url='http://www.tsetmc.com/Loader.aspx?ParTree=111C1417'
s = requests.get(url).text
html=etree.HTML(s)
tr_nodes = html.xpath('//table/tr/td/a[position()<2]')
#header = [i.text for i in tr_nodes] #text=normalizer.normalize('قشرين')
print(type(tr_nodes))
for i in range(2,len(tr_nodes),2):
    namad=normalizer.normalize(str(tr_nodes[i].text))+'\n'
    f.write(namad)
    print(tr_nodes[i].text)
f.close()