import time
from datetime import datetime, timedelta
import threading
import pygame

MP3_PATH = "app/resources/ping.mp3"


def sleep_until_next_minute():
    now = datetime.now()  # timezone handling later
    next_minute = (now.replace(second=0, microsecond=0) + timedelta(minutes=1))
    time.sleep((next_minute - now).total_seconds())


def minute_ping_worker(stop_event: threading.Event, audio_lock: threading.Lock):
    clock = pygame.time.Clock()
    pygame.mixer.music.load(MP3_PATH)

    while not stop_event.is_set():
        sleep_until_next_minute()

        if stop_event.is_set():
            break

        with audio_lock:
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() and not stop_event.is_set():
                clock.tick(10)

def ping(MP3_PATH):
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    pygame.mixer.music.load(MP3_PATH)
    pygame.mixer.music.play()