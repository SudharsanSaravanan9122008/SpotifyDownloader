from multiprocessing.dummy import Process as Proc
import subprocess
import SongHandler
import queue
from constants import *
import os
try:
    os.chdir("./venv/Scripts")
    subprocess.run(["start", ".\\updater.exe"], shell=True)
    os.chdir("../../")
except:
    pass
class Process:
    def __init__(self, parent):
        self.songInfo = {}
        self.state = IDLE
        self.parent = parent
        self.songIndex = None

    def processFunc(self):
        while self.state!=KILL:
            if self.state==WORK:
                songInfo = self.songInfo
                returnCode = SongHandler.downloadSong(songInfo)
                if returnCode == 0:
                    self.markProcessComplete()
                elif returnCode == 1:
                    self.markProcessError("Couldn't query for song", info, index, numTries)
                elif returnCode == 2:
                    self.markProcessError("Couldn't download song", info, index, numTries)
                else:
                    self.markProcessError("Couldn't download album art", info, index, numTries)

            if self.state == COMPLETED:
                self.state = IDLE
                self.songIndex = None
                self.songInfo = []
            elif self.state == ERRORED:
                self.state = IDLE
                self.songIndex = None
                self.songInfo = []
            
            if self.state == IDLE:
                if self.parent.kill:
                    self.state = KILL
                    break
                b, info, index, numTries = self.parent.request()
                if b:
                    self.songInfo = info
                    self.songIndex = index
                    self.state = WORK
        return

    def markProcessComplete(self):
        if self.state!=KILL:
            while self.parent.wait:
                pass
            else:
                self.parent.workerWait = True
                self.parent.songs[self.songIndex]["completed"] = True
                self.parent.songs[self.songIndex]["errorInfo"] = ""
                self.parent.workerWait = False
                
            self.state = COMPLETED

    def markProcessError(self, errorInfo, info, index, numTries):
        if self.state != KILL:
            while self.parent.wait:
                pass
            else:
                if numTries<3:
                    if numTries == 0:
                        self.parent.tryQueue1.put([index, info])
                    elif numTries == 1:
                        self.parent.tryQueue2.put([index, info])
                    elif numTries == 2:
                        self.parent.tryQueue3.put([index, info])
                else:
                    self.parent.workerWait = True
                    self.parent.songs[index]["completed"] = True
                    self.parent.songs[index]["errorInfo"] = errorInfo
                    self.parent.workerWait = False
            self.state = ERRORED

class Parent:
    def __init__(self):
        self.numProcesses = 0
        self.kill = False
        self.songs = []
        self.queue = queue.Queue()
        self.tryQueue1 = queue.Queue()
        self.tryQueue2 = queue.Queue()
        self.tryQueue3 = queue.Queue()
        self.state = None
        self.wait = False
        self.workerWait = False
        self.workers = None

    def request(self):
        if self.queue.empty():
            if self.tryQueue3.empty():
                if self.tryQueue2.empty():
                    if self.tryQueue1.empty():
                        return False, None, None, -1
                    else:
                        i = self.tryQueue1.get()
                        self.tryQueue1.task_done()
                        return True, i[1], i[0], 1
                else:
                    i = self.tryQueue2.get()
                    self.tryQueue2.task_done()
                    return True, i[1], i[0], 2
            else:
                i = self.tryQueue3.get()
                self.tryQueue3.task_done()
                return True, i[1], i[0], 3
        else:
            i = self.queue.get()
            self.queue.task_done()
            return True, i[1], i[0], 0
        
    def start(self, num_processes):
        self.state = IDLE
        processes = []
        workers = []
        for i in range(num_processes):
            worker = Process(self)
            p = Proc(target=worker.processFunc)
            p.start()
            processes.append(p)
            workers.append(worker)
        self.workers = workers
        self.state = STARTED
        is_alive = False
        while not is_alive:
            for i in processes:
                if i.is_alive():
                    is_alive = True
        self.state = COMPLETED

    def getState(self):
        if self.kill:
            return "KILLING"
        elif self.state == COMPLETED:
            return "ENDED"
        elif self.state == IDLE:
            return "IDLE"
        elif self.state == STARTED:
            return "WORKING"
        
    def getSongsProgress(self):
        return self.songs
        
    def addSong(self, songInfo):
        self.wait = True
        i = {
            "name": songInfo["name"],
            "id": songInfo["id"],
            "completed": False,
            "errorInfo": ""
        }
        index = len(self.songs)
        self.songs.append(i)
        self.queue.put([index, songInfo])
        self.wait = False