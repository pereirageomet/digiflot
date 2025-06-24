import logging
logger = logging.getLogger(__name__)

try:
    import vlc
except ImportError:
    VLC_AVAILABLE = False
    logger.warning("The module VLC could not be imported")
else:
    VLC_AVAILABLE = True

import time
import threading
import multiprocessing
from pathlib import Path

# check for mp3-files in the directory of the libs package. If there a no mp3s, search in the parent directory
filePath = Path(__file__).parent
listOfMp3s = [mp3 for mp3 in filePath.glob("*.mp3")]
if len(listOfMp3s) > 0:
    MP3_FILES_AVAILABLE = True
else:
    filePath = filePath.parent
    listOfMp3s = [mp3 for mp3 in filePath.glob("*.mp3")]
    if len(listOfMp3s) > 0:
        MP3_FILES_AVAILABLE = True
    else:
        MP3_FILES_AVAILABLE = False

#global variables
hasbeeped = 0
skimbeeps = True
PlayS = None

def beepOnce():
    if not VLC_AVAILABLE or not MP3_FILES_AVAILABLE:
        logger.warning("VLC module not available")
        return

    global hasbeeped
    if hasbeeped == 0:
        PlayE = threading.Thread(target=PlayEnding, daemon=True)
        PlayE.start()
        hasbeeped +=1

def skimOnce(targett,scrapingFreq):
    if not VLC_AVAILABLE or not MP3_FILES_AVAILABLE:
        logger.warning("VLC module not available")
        return

    global skimbeeps
    global PlayS
    if skimbeeps:
        PlayS = multiprocessing.Process(target=PlaySkim, args = (targett,scrapingFreq,), daemon=True)
        PlayS.start()
        skimbeeps = False
    else:
        PlayS = None

def interruptSkim():
    global PlayS
    try:
        PlayS.terminate() # in case the skimming notification was being played
    except:
        pass

def resetSkimAndBeep():
    global hasbeeped
    global skimbeeps
    hasbeeped = 0
    skimbeeps = True

def PlayEnding():
    if not VLC_AVAILABLE or not MP3_FILES_AVAILABLE:
        logger.warning("VLC module not available")
        return
   
    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(str(filePath/"beep-sound-8333.mp3"))
    player.set_media(media)
    player.play()

def PlaySkim(totaltime = 5,Freq=5):
    if not VLC_AVAILABLE or not MP3_FILES_AVAILABLE:
        logger.warning("VLC module not available")
        return

    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(str(filePath/"button-13.mp3"))
    for _ in range(round(totaltime/Freq)):
        time.sleep(Freq)
        player.set_media(media)
        player.play()

def playFinish():
    if not VLC_AVAILABLE or not MP3_FILES_AVAILABLE:
        logger.warning("VLC module not available")
        return

    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(str(filePath/"finish.mp3"))
    player.set_media(media)
    player.play()

# for testing
def main():
    skimOnce(targett=100)
    time.sleep(1)
    playFinish()
    time.sleep(1)
    PlaySkim()
    time.sleep(1)
    PlayEnding()
    time.sleep(1)
    

if __name__ == "__main__":
    main()