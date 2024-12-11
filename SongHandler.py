import math
import json
import urllib.request as ur
import spotipy
import os
from spotipy.oauth2 import SpotifyClientCredentials
from pytubefix import YouTube
from pytubefix.innertube import _default_clients
import youtubesearchpython as ysp
from constants import *

# os.chdir(os.environ["HOME"])

def makeDir(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)
makeDir(PARENT_DIR)
makeDir(SONG_OUTPUT_DIR)
makeDir(IMAGES_OUTPUT_DIR)
makeDir(METADATA_OUTPUT_DIR)
makeDir(PLAYLIST_OUTPUT_DIR)

os.environ["SPOTIPY_CLIENT_ID"] = "7ae80ed0486a4021a296da8e6bbe307a"
os.environ["SPOTIPY_CLIENT_SECRET"] = "83a55cc933c845c3a604760902811fd9"

auth_manager = SpotifyClientCredentials()
sp = spotipy.Spotify(auth_manager=auth_manager)

_default_clients["ANDROID_MUSIC"] = _default_clients["ANDROID_CREATOR"]

def convert_to_seconds(time_string):
    time_parts = list(map(int, time_string.split(":")))
    if len(time_parts) == 3:
        hours, minutes, seconds = time_parts
        total_seconds = hours * 3600 + minutes * 60 + seconds
    elif len(time_parts) == 2:
        minutes, seconds = time_parts
        total_seconds = minutes * 60 + seconds
    return total_seconds

def downloadSong(songInfo):

    def queryYt(songName, songLength, artists):
        query = songName +" by "+ artists + " lyric"
        search = ysp.CustomSearch(query, ysp.VideoSortOrder.relevance, limit=3)
        searchResult = search.result()["result"]
        relativeDuration = []
        for i in searchResult:
            relativeDuration.append(abs(songLength - convert_to_seconds(i["duration"])))
        relativeDuration.sort()
        for i in searchResult:
            if relativeDuration[0] == abs(songLength - convert_to_seconds(i["duration"])):
                result = i
                break
        return result["id"]

    def downloadSongYt(id, fileName, directory):
        try:
            streams = YouTube("https://www.youtube.com/watch?v="+id).streams.filter(only_audio=True, audio_codec="opus")
            highest = streams[0]
            for i in streams:
                if int(highest.abr[-len(highest.abr)-1: -4]) < int(i.abr[-len(highest.abr)-1: -4]):
                    highest = i
            streams.get_by_itag(highest.itag).download(directory, fileName+".webm", skip_existing=True)
        except Exception as e:
            print(e)
            return 1
        return 0
    
    try:
        query = queryYt(songInfo["name"], songInfo["duration"], songInfo["artists"])
    except Exception as e:
        print(e)
        return 1
    
    retCode = downloadSongYt(query, songInfo["id"], SONG_OUTPUT_DIR)
    if retCode != 0:
        return 2
    
    imageFileName = songInfo["image"].split('/')[-1]
    ret3 = False
    try:
        ur.urlretrieve(songInfo["image"], IMAGES_OUTPUT_DIR+imageFileName)
    except:
        songInfo["imageFilename"] = ""
        ret3 = True
    
    with open(METADATA_OUTPUT_DIR+songInfo["id"]+".json", 'w') as file:
        json.dump(songInfo, indent=True, fp=file)
    if ret3:
        return 3
    else:
        return 0

def extractEssentials(songInfo):
    id = songInfo["id"]
    images = songInfo["album"]["images"]
    imageUrl = images[0]["url"]
    artistsList = songInfo["artists"]
    artists = ""
    for i in artistsList:
        artists += i["name"]
        artists += ", "
    artists = artists[0: len(artists) - 2]
    duration = math.floor(songInfo["duration_ms"]/1000)
    name = songInfo["name"]
    try:
        previewUrl = songInfo["preview_url"]
    except:
        previewUrl = ""
    track = {
        "name": name,
        "artists": artists,
        "image": imageUrl,
        "imageFileName": imageUrl.split('/')[-1],
        "imageUrl": imageUrl,
        "duration": duration,
        "preview": previewUrl,
        "id": id
    }
    return track

def getSongInfoFromTrack(trackId):
    track = extractEssentials(sp.track(trackId))
    return track

def getSongsInfoFromPlaylist(playlistLink, saveplaylistInfo):
    playlistItems = []
    playList = sp.playlist(playlistLink)
    playListInfo = {
        "name": playList["name"],
        "id": playList["id"],
        "image": playList["images"][0]["url"],
        "total": playList["tracks"]["total"]
    }
    offset = 0
    while offset<playListInfo["total"]:
        items = sp.playlist_tracks(playlistLink, offset=offset)
        for i in items["items"]:
            playlistItems.append(extractEssentials(i["track"]))
        offset+=100
    if saveplaylistInfo:
        with open(PLAYLIST_OUTPUT_DIR+playList["id"]+'.json', 'w') as f:
            json.dump({
                "info": playListInfo,
                "tracks": playlistItems
            }, f, indent=True)
            f.close()

    return playlistItems

def searchSongs(name):
    f = os.listdir(METADATA_OUTPUT_DIR)
    songs = []
    for i in f:
        with open(os.path.join(METADATA_OUTPUT_DIR,i), 'r') as file:
            d = json.load(file)
            name.lower()
            n = d["name"]
            d["name"].lower()
            if name in d["name"]:
                songs.append((i[:-5], n))
    return songs
