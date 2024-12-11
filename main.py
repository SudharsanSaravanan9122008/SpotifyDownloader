import os
# os.chdir(os.environ["HOME"])
import subprocess
import SongHandler
from ProcessHandler import Parent
from multiprocessing.dummy import Process
import json

app = Parent()
parentDir = "./"
def createApp(numProcesses):
    Process(target=app.start, args=(numProcesses, )).start()


def isAppCreated():
    if app.state == None:
        return False
    else:
        return True

def addItem(link):
    if isAppCreated():
        if "track" in link:
            app.addSong(SongHandler.getSongInfoFromTrack(link))
            return 0
        elif "playlist" in link:
            items = SongHandler.getSongsInfoFromPlaylist(link, True)
            for i in items:
                app.addSong(i)
            return 0
        else:
            return 1
    
def killApp():
    if isAppCreated():
        app.kill = True

def getState():
    if isAppCreated():
        return app.getState()
    else:
        return ""
    
def getInfo(link):
    if "playlist" in link:
        return json.dumps({
            "type": "playlist",
            "songInfo": SongHandler.getSongsInfoFromPlaylist(link, False)
        })
    elif "track" in link:
        return json.dumps({
            "type": "track",
            "songInfo": SongHandler.getSongInfoFromTrack(link)
        })
    else:
        return json.dumps({"type": None})
    
def getSongsProgress():
    if isAppCreated():
        return json.dumps({
            "songsProgress": app.songs
        })
    else:
        return json.dumps({
            "songsProgress": None
        })
    
def searchSongs(name):
    songs = SongHandler.searchSongs(name)
    if len(songs):
        print("Search results:")
        for i in songs:
            print("\t" + " - ".join(i))
    else:
        print("No results found")

def playSong(name):
    if os.path.exists(os.path.join(parentDir, SongHandler.METADATA_OUTPUT_DIR[2:], name+".json")):
        subprocess.run(["start", f'{os.path.join(parentDir, SongHandler.SONG_OUTPUT_DIR[2:], name+".webm")}'], shell=True)
        subprocess.run(["notepad", f'{os.path.join(parentDir, SongHandler.METADATA_OUTPUT_DIR[2:], name+".json")}'], shell=True)

while True:
    g=eval(input(">>>"))
    if g:
        print(g)