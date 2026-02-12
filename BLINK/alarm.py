import pygame
import threading
import os

pygame.mixer.init()

SOUND_FILE = "Beep.mp3"

def play_sound():
    try:
        if os.path.exists(SOUND_FILE):
            pygame.mixer.music.load(SOUND_FILE)
            pygame.mixer.music.play()
        else:
            print("Sound file not found")
    except Exception as e:
        print("Sound error:", e)

def trigger_alarm():
    threading.Thread(target=play_sound, daemon=True).start()