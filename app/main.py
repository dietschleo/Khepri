
import threading
import pygame
from src.alarm import minute_ping_worker
from src.scheduler import Scheduler


def main():
    pygame.mixer.init()

    stop_event = threading.Event()
    audio_lock = threading.Lock()

    ping_thread = threading.Thread(
        target=minute_ping_worker,
        args=(stop_event, audio_lock),
        daemon=True,
    )
    ping_thread.start()

    try:
        # Other program logic runs in parallel here
        while True:
            # Replace with your real work loop
            #time.sleep(0.1)
            print("Main thread is running...")
            

    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        ping_thread.join(timeout=2)
        pygame.mixer.quit()


if __name__ == "__main__":
    main()
