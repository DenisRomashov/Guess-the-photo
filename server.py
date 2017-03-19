# coding=UTF-8
import sys
import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import urlparse
import requests
import random
import re


class cache():
 def __init__(self):
  self.cache={}
  # создаем словарь
 
 def yandex(self, name):
   resp=requests.get('https://yandex.ru/images/search?type=face&text=%s' % name)
   # выполняем запрос на поиск и получаем что то вроде html кода
   urls=re.findall('(?<=img_url=)http%3a%2f%2f.*?(?=&)',resp.text, flags=re.I)   
   # выполняем поиск по полученному выше коду, и получаем список всех найденных совпадений
   urls=[re.sub('%2f','/',u,flags=re.I) for u in urls]   
   urls=[re.sub('%3a',':',u,flags=re.I) for u in urls]
   # заменяем все %2f на /, а %3a на :
   # так как после re.findall у нас будут ссылки вида 
   # http%3A%2F%2Fp2pnet.ru%2Fimg%2F2016%2F010604%2F5813174
   # а нам нужно получить нормальную ссылку вида
   # http://p2pnet.ru/img/2016/010604/5813174
   # flags=re.I - игнорировать регистр
   return urls
 # поиск в яндексе. Получаем НАБОР ссылок на изображения.
   

 def person(self, name):    
   urls=self.yandex(name)
   urls_spisok=[]
   for i in urls:
    if i not in urls_spisok: urls_spisok.append(i)   
   self.cache[name]=urls_spisok  
   # получаем СПИСОК ссылок на изображения
   return self.cache[name]

  
  
  
  
  
  
  
class ans():
 ans_tmpl='<input type="radio" name="answer" value="%s">%s<br>\n'
 # строка, которая будет в дальнейшем интергрироваться в страницу
 
 def __init__(self):
  with open('files/_names.txt', 'r') as f:
   self.names=f.read()
   self.names=self.names.splitlines()
   self.curr_names=[]
   self.curr_ans=""
   self.curr_link=""
   # обрабатываем файл _names и создаем список имён  
   
   self.cache=cache()
   # создание экземпляра класса cache

 def newans(self, num):
  if not num:
    num=10
  # если зайти не на главную страницу(menu), а сразу на game.html
  # то из за отсутствия параметра diff(numb), страница не откроется
  # из за ошибок... Таким вот образом я это пофиксил...
  self.curr_names=self.names[:num]
  # создаем список из первых NUM имён (10,50,100)
  self.curr_ans=random.choice(self.curr_names)
  # выбираем имя, которое будем угадывать
  self.curr_link=random.choice(self.cache.person(self.curr_ans))
  # получаем ОДНУ ссылку на изображение данного персонажа
  
 def formatted(self):
  f=""
  for i in self.curr_names: f+=self.ans_tmpl % (i, i)
  # создаем html код со списком всех имен
  return f
  
  
class myHandler(SimpleHTTPRequestHandler):
    ans=ans()
	# создание экземпляра класса ans
        
    def do_GET(self):
        parsed=urlparse.urlparse(self.path)
		#парсим url.  scheme://netloc/path;parameters?query#fragment
        params=urlparse.parse_qs(parsed.query)
		# параметры ссылки (query) разделяем и заносим в словарь		
        data=""
		
        if parsed.path == '/result.html' and 'answer' in params:
        # если мы на странице result.html и в параметрах есть answer, то
        # P.S. если answer нету, то мы попадаем в "menu"
            with open('files'+parsed.path, 'rb') as fd:
                data=fd.read()
        # открываем файл result.html в двоичном режиме
            data=data.replace('##PERSON##', self.ans.curr_ans)
            if self.ans.curr_ans in params['answer']:
                data=data.replace('##RESULT##', 'WIN<br><br><img  src="http://icons.iconarchive.com/icons/gakuseisean/ivista-2/128/Alarm-Tick-icon.png"/>')
            else:
                data=data.replace('##RESULT##', 'LOSE<br><br><img  src="http://icons.iconarchive.com/icons/gakuseisean/ivista-2/128/Alarm-Error-icon.png"/>')
        # проверяем совпал ли правильный ответ с тем, что был выбран. В соответствии с этим, делаем нужный вывод.

		
        elif parsed.path == '/game.html':
            with open('files'+parsed.path, 'rb') as fd:
                data=fd.read()            
            numb=len(self.ans.curr_names)
            if 'diff' in params:
                try:
                    numb=int(params['diff'][0])
                except:
                    pass
            # если был переход в "меню", то при выборе сложности передается параметр diff, если он присутствует в url
			# тогда, устанавливаем numb=diff. Если был переход по кнопке "продолжить", тогда diff не передается, и мы
			# оставляем всё как есть
            self.ans.newans(numb)
			# формируем список имён
            data=data.replace('##LINK##', self.ans.curr_link.encode('ascii'))
			# вставка ссылк на изображение угадываемой персоны
            data=data.replace('##ANSWERS##', self.ans.formatted().encode('ascii'))
			# вывод всех вариантов ответа в формате html
			        
        else:
            with open('files/menu.html', 'rb') as fd:
                data=fd.read()
            # если же мы на страница menu.html, то на ней нам ничего менять не нужно. 
            # она ничего не получает посредством GET запроса. Поэтому выводим как есть.
			
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()		
        self.wfile.write(data)
		# выводим полученный html код
		

def main():
    try:    
      httpd = BaseHTTPServer.HTTPServer(('localhost', 1337), myHandler)
	  # создаём и запускаем сервер 
      sa = httpd.socket.getsockname()
      print "Serving HTTP on", sa[0], "port", sa[1], "..."
	  # выводим адрес сервера и инфу о том, что сервер запущен
      httpd.serve_forever()
	  # начинаем обрабатывать запросы

    except KeyboardInterrupt:      	
      httpd.socket.close();    
      print "EXIT! Ctrl+C pressed! Server stopped."	
      raw_input("Press Enter to continue...")	  
	  # вырубаем сервер в случае нажатия CTRL + C/BREAK
      
		
if __name__ == '__main__':
     main()
