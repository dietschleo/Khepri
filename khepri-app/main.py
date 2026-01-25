import time
import pygame
from datetime import datetime, timedelta


def main():
    MP3_PATH = "khepri-app/resources/ping.mp3"

    pygame.mixer.init()
    pygame.mixer.music.load(MP3_PATH)
    clock = pygame.time.Clock()

    def wait_until_next_minute():
        now = datetime.now() #handle time zone later
        next_minute = (now.replace(second=0, microsecond=0)
                    + timedelta(minutes=1))
        time.sleep((next_minute - now).total_seconds())

    while True:
        wait_until_next_minute()
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            clock.tick(10)    

if __name__ == "__main__":
    main()
