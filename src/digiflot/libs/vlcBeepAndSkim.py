"""
Audio notification module using VLC player.

Provides functions for playing beep sounds and skimming notifications
using VLC media player. Automatically locates MP3 files in the libs
directory or parent directory.

Global variables:
    hasbeeped: Tracks whether beep has been played
    skimbeeps: Controls whether skimming notifications are enabled
    PlayS: Reference to the skimming process
"""
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
    """
    Play a single beep sound if not already played in this session.

    Creates a threading.Thread to play the ending beep sound using VLC.
    Only plays if hasbeeped is 0, then increments the counter.
    """
    if not VLC_AVAILABLE or not MP3_FILES_AVAILABLE:
        logger.warning("VLC module not available")
        return

    global hasbeeped
    if hasbeeped == 0:
        PlayE = threading.Thread(target=PlayEnding, daemon=True)
        PlayE.start()
        hasbeeped +=1

def skimOnce(targett,scrapingFreq):
    """
    Start skimming notifications if enabled.

    Launches a multiprocessing.Process to play beep sounds at regular
    intervals during a skimming operation. Only starts if skimbeeps is True.

    Args:
        targett: Total duration for skimming
        scrapingFreq: Frequency of beep notifications
    """
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
    """
    Interrupt any currently playing skimming notification.

    Attempts to terminate the PlayS multiprocessing process if it's running.
    """
    global PlayS
    try:
        PlayS.terminate() # in case the skimming notification was being played
    except:
        pass

def resetSkimAndBeep():
    """
    Reset beep and skimming state for a new session.

    Clears the hasbeeped counter and re-enables skimbeeps.
    """
    global hasbeeped
    global skimbeeps
    hasbeeped = 0
    skimbeeps = True

def PlayEnding():
    """
    Play the ending beep sound using VLC.

    Creates a VLC instance, loads the beep sound MP3, and starts playback.
    Uses a daemon thread so it doesn't block program exit.
    """
    if not VLC_AVAILABLE or not MP3_FILES_AVAILABLE:
        logger.warning("VLC module not available")
        return
   
    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(str(filePath/"beep-sound-8333.mp3"))
    player.set_media(media)
    player.play()

def PlaySkim(totaltime = 5,Freq=5):
    """
    Play skimming beep notifications at regular intervals.

    Plays the button beep MP3 repeatedly at the specified frequency
    for the total duration.

    Args:
        totaltime: Total duration in seconds (default: 5)
        Freq: Interval between beeps in seconds (default: 5)
    """
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
    """
    Play the finish sound using VLC.

    Creates a VLC instance, loads the finish MP3, and starts playback.
    """
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
    """
    Main function for testing the audio notification module.

    Demonstrates skimming notifications and all available sounds.
    """
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
