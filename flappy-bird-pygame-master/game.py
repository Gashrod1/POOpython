import pygame
import os
from pygame.locals import *
from bird import *
from pipepair import *
from collections import deque


BRIGHT = (255, 255, 255)
FONTSIZE = 32


class Game:
    def __init__(self) -> None:
        pygame.init()

        self.display_surface = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        pygame.display.set_caption("Pygame Flappy Bird")

        self.clock = pygame.time.Clock()
        self.score_font = pygame.font.SysFont(None, FONTSIZE, bold=True)  # default font
        self.images = self.load_images()

        # the bird stays in the same x position, so bird.x is a constant
        # center bird on screen
        self.bird = Bird(
            50,
            int(WIN_HEIGHT / 2 - Bird.HEIGHT / 2),
            2,
            (self.images["bird-wingup"], self.images["bird-wingdown"]),
        )

        self.pipes = deque()

        self.frame_clock = (
            0  # this counter is only incremented if the game isn't paused
        )
        self.score = 0
        self.done = False
        self.paused = False

    def load_images(self):
        def load_image(img_file_name):
            file_name = os.path.join(os.path.dirname(__file__), "images", img_file_name)
            img = pygame.image.load(file_name)
            img.convert()
            return img

        return {
            "background": load_image("background.png"),
            "pipe-end": load_image("pipe_end.png"),
            "pipe-body": load_image("pipe_body.png"),
            "bird-wingup": load_image("bird_wing_up.png"),
            "bird-wingdown": load_image("bird_wing_down.png"),
        }

    def is_ended(self):
        return self.done

    def handle_events(self) -> None:
        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                self.done = True
                break
            elif e.type == KEYUP and e.key in (K_PAUSE, K_p):
                self.paused = not self.paused
            elif e.type == MOUSEBUTTONUP or (
                e.type == KEYUP and e.key in (K_UP, K_RETURN, K_SPACE)
            ):
                self.bird.msec_to_climb = Bird.CLIMB_DURATION

    def update_world(self) -> None:
        if not (
            self.paused or self.frame_clock % msec_to_frames(PipePair.ADD_INTERVAL, FPS)
        ):
            pp = PipePair(self.images["pipe-end"], self.images["pipe-body"])
            self.pipes.append(pp)

        if not self.paused:
            pipe_collision = any(p.collides_with(self.bird) for p in self.pipes)
            if (
                pipe_collision
                or 0 >= self.bird.y
                or self.bird.y >= WIN_HEIGHT - Bird.HEIGHT
            ):
                self.done = True

            while self.pipes and not self.pipes[0].visible:
                self.pipes.popleft()

            for p in self.pipes:
                p.update()

            self.bird.update()

            for p in self.pipes:
                if p.x + PipePair.WIDTH < self.bird.x and not p.score_counted:
                    self.score += 1
                    p.score_counted = True

    def render_world(self) -> None:
        for x in (0, WIN_WIDTH / 2):
            self.display_surface.blit(self.images["background"], (x, 0))

        for p in self.pipes:
            self.display_surface.blit(p.image, p.rect)

        self.display_surface.blit(self.bird.image, self.bird.rect)

        score_surface = self.score_font.render(str(self.score), True, BRIGHT)
        score_x = WIN_WIDTH / 2 - score_surface.get_width() / 2
        self.display_surface.blit(score_surface, (score_x, PipePair.PIECE_HEIGHT))

        pygame.display.flip()
        self.frame_clock += 1


if __name__ == "__main__":
    screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    game = Game()

    while not game.is_ended():
        game.handle_events()
        game.update_world()
        game.render_world()
        game.clock.tick(FPS)
