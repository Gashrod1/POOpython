#! /usr/bin/env python3

"""Flappy Bird, implemented using Pygame."""

import math
import os
from random import randint
from collections import deque

import pygame
from pygame.locals import *


FPS = 60
TILE = 284
ANIMATION_SPEED = 0.18  # pixels per millisecond
WIN_WIDTH = TILE * 2  # BG image size: 284x512 px; tiled twice
WIN_HEIGHT = 512
BRIGHT = (255, 255, 255)
FONTSIZE = 32


class Bird(pygame.sprite.Sprite):
    """Represents the bird controlled by the player.

    The bird is the 'hero' of this game.  The player can make it climb
    (ascend quickly), otherwise it sinks (descends more slowly).  It must
    pass through the space in between pipes (for every pipe passed, one
    point is scored); if it crashes into a pipe, the game ends.

    Attributes:
    x: The bird's X coordinate.
    y: The bird's Y coordinate.
    msec_to_climb: The number of milliseconds left to climb, where a
        complete climb lasts Bird.CLIMB_DURATION milliseconds.

    Constants:
    WIDTH: The width, in pixels, of the bird's image.
    HEIGHT: The height, in pixels, of the bird's image.
    SINK_SPEED: With which speed, in pixels per millisecond, the bird
        descends in one second while not climbing.
    CLIMB_SPEED: With which speed, in pixels per millisecond, the bird
        ascends in one second while climbing, on average.  See also the
        Bird.update docstring.
    CLIMB_DURATION: The number of milliseconds it takes the bird to
        execute a complete climb.
    """

    WIDTH = HEIGHT = 32
    SINK_SPEED = 0.18
    CLIMB_SPEED = 0.3
    CLIMB_DURATION = 333.3

    def __init__(self, x, y, msec_to_climb, images):
        """Initialise a new Bird instance.

        Arguments:
        x: The bird's initial X coordinate.
        y: The bird's initial Y coordinate.
        msec_to_climb: The number of milliseconds left to climb, where a
            complete climb lasts Bird.CLIMB_DURATION milliseconds.  Use
            this if you want the bird to make a (small?) climb at the
            very beginning of the game.
        images: A tuple containing the images used by this bird.  It
            must contain the following images, in the following order:
                0. image of the bird with its wing pointing upward
                1. image of the bird with its wing pointing downward
        """
        super(Bird, self).__init__()
        self.x, self.y = x, y
        self.msec_to_climb = msec_to_climb
        self._img_wingup, self._img_wingdown = images
        self._mask_wingup = pygame.mask.from_surface(self._img_wingup)
        self._mask_wingdown = pygame.mask.from_surface(self._img_wingdown)

    def update(self, delta_frames=1):
        """Update the bird's position.

        This function uses the cosine function to achieve a smooth climb:
        In the first and last few frames, the bird climbs very little, in the
        middle of the climb, it climbs a lot.
        One complete climb lasts CLIMB_DURATION milliseconds, during which
        the bird ascends with an average speed of CLIMB_SPEED px/ms.
        This Bird's msec_to_climb attribute will automatically be
        decreased accordingly if it was > 0 when this method was called.

        Arguments:
        delta_frames: The number of frames elapsed since this method was
            last called.
        """
        if self.msec_to_climb > 0:
            frac_climb_done = 1 - self.msec_to_climb / Bird.CLIMB_DURATION
            self.y -= (
                Bird.CLIMB_SPEED
                * frames_to_msec(delta_frames)
                * (1 - math.cos(frac_climb_done * math.pi))
            )
            self.msec_to_climb -= frames_to_msec(delta_frames)
        else:
            self.y += Bird.SINK_SPEED * frames_to_msec(delta_frames)

    @property
    def image(self) -> pygame.surface.Surface:
        """Get a Surface containing this bird's image.

        This will decide whether to return an image where the bird's
        visible wing is pointing upward or where it is pointing downward
        based on pygame.time.get_ticks().  This will animate the flapping
        bird, even though pygame doesn't support animated GIFs.
        """
        if pygame.time.get_ticks() % 500 >= 250:
            return self._img_wingup

        else:
            return self._img_wingdown

    @property
    def mask(self) -> pygame.mask.Mask:
        """Get a bitmask for use in collision detection.

        The bitmask excludes all pixels in self.image with a
        transparency greater than 127."""
        if pygame.time.get_ticks() % 500 >= 250:
            return self._mask_wingup
        else:
            return self._mask_wingdown

    @property
    def rect(self) -> pygame.rect.Rect:
        """Get the bird's position, width, and height, as a pygame.Rect."""
        return Rect(self.x, self.y, Bird.WIDTH, Bird.HEIGHT)


class PipePair(pygame.sprite.Sprite):
    """Represents an obstacle.

    A PipePair has a top and a bottom pipe, and only between them can
    the bird pass -- if it collides with either part, the game is over.

    Attributes:
    x: The PipePair's X position.  This is a float, to make movement
        smoother.  Note that there is no y attribute, as it will only
        ever be 0.
    image: A pygame.Surface which can be blitted to the display surface
        to display the PipePair.
    mask: A bitmask which excludes all pixels in self.image with a
        transparency greater than 127.  This can be used for collision
        detection.
    top_pieces: The number of pieces, including the end piece, in the
        top pipe.
    bottom_pieces: The number of pieces, including the end piece, in
        the bottom pipe.

    Constants:
    WIDTH: The width, in pixels, of a pipe piece.  Because a pipe is
        only one piece wide, this is also the width of a PipePair's
        image.
    PIECE_HEIGHT: The height, in pixels, of a pipe piece.
    ADD_INTERVAL: The interval, in milliseconds, in between adding new
        pipes.
    """

    WIDTH = 80
    PIECE_HEIGHT = 32
    ADD_INTERVAL = 3000

    def __init__(self, pipe_end_img, pipe_body_img):
        """Initialises a new random PipePair.

        The new PipePair will automatically be assigned an x attribute of
        float(WIN_WIDTH - 1).

        Arguments:
        pipe_end_img: The image to use to represent a pipe's end piece.
        pipe_body_img: The image to use to represent one horizontal slice
            of a pipe's body.
        """
        self.x = float(WIN_WIDTH - 1)
        self.score_counted = False

        self.image = pygame.Surface((PipePair.WIDTH, WIN_HEIGHT), SRCALPHA)
        self.image.convert()  # speeds up blitting
        self.image.fill((0, 0, 0, 0))
        total_pipe_body_pieces = int(
            (
                WIN_HEIGHT
                - 3 * Bird.HEIGHT  # fill window from top to bottom
                - 3 * PipePair.PIECE_HEIGHT  # make room for bird to fit through
            )
            / PipePair.PIECE_HEIGHT  # 2 end pieces + 1 body piece  # to get number of pipe pieces
        )
        self.bottom_pieces = randint(1, total_pipe_body_pieces)
        self.top_pieces = total_pipe_body_pieces - self.bottom_pieces

        # bottom pipe
        for i in range(1, self.bottom_pieces + 1):
            piece_pos = (0, WIN_HEIGHT - i * PipePair.PIECE_HEIGHT)
            self.image.blit(pipe_body_img, piece_pos)
        bottom_pipe_end_y = WIN_HEIGHT - self.bottom_height_px
        bottom_end_piece_pos = (0, bottom_pipe_end_y - PipePair.PIECE_HEIGHT)
        self.image.blit(pipe_end_img, bottom_end_piece_pos)

        # top pipe
        for i in range(self.top_pieces):
            self.image.blit(pipe_body_img, (0, i * PipePair.PIECE_HEIGHT))
        top_pipe_end_y = self.top_height_px
        self.image.blit(pipe_end_img, (0, top_pipe_end_y))

        # compensate for added end pieces
        self.top_pieces += 1
        self.bottom_pieces += 1

        # for collision detection
        self.mask = pygame.mask.from_surface(self.image)

    @property
    def top_height_px(self) -> int:
        """Get the top pipe's height, in pixels."""
        return self.top_pieces * PipePair.PIECE_HEIGHT

    @property
    def bottom_height_px(self) -> int:
        """Get the bottom pipe's height, in pixels."""
        return self.bottom_pieces * PipePair.PIECE_HEIGHT

    @property
    def visible(self) -> bool:
        """Get whether this PipePair on screen, visible to the player."""
        return -PipePair.WIDTH < self.x < WIN_WIDTH

    @property
    def rect(self) -> pygame.rect.Rect:
        """Get the Rect which contains this PipePair."""
        return Rect(self.x, 0, PipePair.WIDTH, PipePair.PIECE_HEIGHT)

    def update(self, delta_frames=1):
        """Update the PipePair's position.

        Arguments:
        delta_frames: The number of frames elapsed since this method was
            last called.
        """
        self.x -= ANIMATION_SPEED * frames_to_msec(delta_frames)

    def collides_with(self, bird):
        """Get whether the bird collides with a pipe in this PipePair.

        Arguments:
        bird: The Bird which should be tested for collision with this
            PipePair.
        """
        return pygame.sprite.collide_mask(self, bird)


def frames_to_msec(frames, fps=FPS) -> float:
    """Convert frames to milliseconds at the specified framerate.

    Arguments:
    frames: How many frames to convert to milliseconds.
    fps: The framerate to use for conversion.  Default: FPS.
    """
    return 1000.0 * frames / fps


def msec_to_frames(milliseconds, fps=FPS) -> float:
    """Convert milliseconds to frames at the specified framerate.

    Arguments:
    milliseconds: How many milliseconds to convert to frames.
    fps: The framerate to use for conversion.  Default: FPS.
    """
    return fps * milliseconds / 1000.0


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
            self.paused or self.frame_clock % msec_to_frames(PipePair.ADD_INTERVAL)
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
