# DSS course project
first create : sahamyabConfig.ini
```
[Sahamyab]
username = 
password = 

[DEFAULT]
ServerAliveInterval = 45
```
to run sahamyab crawler :

1- cd sahamyab

2-run this code

```
scrapy crawl sahamyabComments -o data.json
```

you should install [scrapy](https://docs.scrapy.org/en/latest/intro/install.html)
