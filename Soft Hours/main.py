import pygame
import sys
from game import Game

def main():
    pygame.init()
    pygame.mixer.init()

    INTERNAL_W, INTERNAL_H = 1280, 720

    screen = pygame.display.set_mode((INTERNAL_W, INTERNAL_H))
    pygame.display.set_caption("Soft Hours")

    clock = pygame.time.Clock()
    FPS   = 60

    game = Game(screen, INTERNAL_W, INTERNAL_H)

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            game.handle_event(event)

        game.update(dt)
        game.draw()

        pygame.display.flip()

if __name__ == "__main__":
    main()
