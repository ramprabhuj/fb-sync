from BaseHTTPServer import HTTPServer
import os.path
import facebook
import time
import webbrowser
import os
import urllib
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import urllib2
import shutil
from threading import Timer
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

__author__="ramprabhuj"
__date__ ="$Jan 29, 2011 6:02:11 PM$"


# Register the streaming http handlers with urllib2
register_openers()

#Need to invoke the browser and get a auth token
access_token = ""

default_args = ""

def init():
    global default_args
    global fb
    global access_token
    args = {}
    args["access_token"] = access_token;
    default_args = urllib.urlencode(args)
    fb = facebook.GraphAPI(access_token);

def create_album(path):
    album = os.path.basename(path)
    print album
    print access_token
    fb.put_object("me","albums",name=album,message="")

def get_album_id(albums,name):
    for album in albums:
        if album["name"].lower() == name.lower():
            return album["id"]

temp = {}

def upload_photo(photo):
    dir   = os.path.dirname(photo)
    album = os.path.basename(dir)
    photo_name = os.path.basename(photo)
    albums = fb.get_connections("me","albums")["data"]
    datagen, headers = multipart_encode({"message":"test pic","source": open(photo)})
    request = urllib2.Request("https://graph.facebook.com/" + get_album_id(albums,album) + "/photos?"+default_args, datagen, headers)    
    id = fb.parse_json(urllib2.urlopen(request).read())
    temp["id"] = id["id"]
    shutil.move(photo, dir + "/" + id["id"] + photo_name[photo_name.rindex("."):])
    
def handle_fs_events(event):
    if event.event_type == "created":
        if event.is_directory:
            create_album(event.src_path)
        else:
            id = os.path.basename(event.src_path)
            if temp.has_key(id):
                del temp[id]
            else:
                upload_photo(event.src_path)
    

def start_fs_loop():
    init()
    try:
        os.makedirs("albums")
    except:
        None
    ev_handler = FileSystemEventHandler()
    ev_handler.dispatch = handle_fs_events

    event_handler = LoggingEventHandler()
    observer = Observer()
    observer.schedule(ev_handler, "albums/", recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

authenticated = False

def persist_token():
    None
    
def check_access_token():
    if(access_token == ''):
        server = HTTPServer(('',11235),ServerHandler)
        print "Opening web browser"
        webbrowser.open_new_tab("http://localhost:11235/")
        while authenticated == False:
            server.handle_request()
        print "Starting FS Loop"
        start_fs_loop()
    else:
        start_fs_loop()
    

def sync_photos():
    feeds = fb.get_connections("me","albums");

    for feed in feeds["data"]:
        os.removedirs("albums/" + feed["name"])
        os.mkdir("albums/" + feed["name"])
        photos = fb.get_connections(feed["id"],"photos")
        for photo in photos["data"]:
            conn = urllib.urlopen(photo["source"] + default_args)
            data = conn.read()
            file = open("albums/" + feed["name"] + "/" + photo["id"],"w")
            file.write(data)
            file.close()
            break
        break


class ServerHandler(BaseHTTPRequestHandler):
    f = open('login.html')
    login = f.read()
    f.close()

    f = open('access.html')
    access = f.read()
    f.close()

    def do_GET(self):
        global authenticated
        global access_token

        try:
            self.path.index("code")
            self.send_response(200)
            self.send_header("Content-type" ,"text/html")
            self.end_headers()
            self.wfile.write(self.access)
        except(ValueError):
            try:
                self.path.index('fbaccess')
                authenticated = True
                access_token = self.path[self.path.index("access_token=") + 13:]
                access_token = access_token[:access_token.index("&")]
                self.send_response(200)
                self.send_header("Content-type" ,"text/html")
                self.end_headers()
                self.wfile.write('<body><script>window.close();</script></body>')
            except(ValueError):
                self.send_response(200)
                self.send_header("Content-type" ,"text/html")
                self.end_headers()
                self.wfile.write(self.login)
        
if __name__ == "__main__":
    check_access_token()
