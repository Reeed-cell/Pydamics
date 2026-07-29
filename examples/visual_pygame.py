"""
Visual demo #2: pygame interactive window.

Real interactive simulation -- click to drop a new ball anywhere, watch
gravity + drag + floor bounces play out live. Uses the engine's
auto-run mode (world.run()) so physics steps on its own background
thread while pygame just reads positions and draws each frame.

Run with:  python examples/visual_pygame.py
Controls:  click anywhere to drop a ball, ESC or close window to quit.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import random
import pygame

from pydamics import Entity, World

WIDTH, HEIGHT = 800, 600
PPU = 40           # pixels per world-unit
RADIUS_WORLD = 0.4
RADIUS_PX = int(RADIUS_WORLD * PPU)
FLOOR_Y_WORLD = 0.0
BOUNCE_DAMPING = 0.65

COLORS = [(230, 57, 70), (69, 123, 157), (42, 157, 143), (244, 162, 97), (155, 93, 229)]


def world_to_screen(pos):
    """World coords (y-up, origin at floor) -> screen pixels (y-down)."""
    sx = pos.x * PPU
    sy = HEIGHT - (pos.y * PPU)
    return int(sx), int(sy)


def screen_to_world_x(px):
    return px / PPU


def make_ball(world, x_world, y_world):
    e = Entity(mass=random.uniform(0.5, 2.0), position=(x_world, y_world))
    e.physics2d.gravity(force=9.8)
    e.physics2d.fluid(density=1.0, drag=random.uniform(0.05, 0.3))
    e.color = random.choice(COLORS)
    world.add(e)
    return e


def bounce_check(world, dt):
    for e in world.entities:
        if e.position.y - RADIUS_WORLD < FLOOR_Y_WORLD:
            e.position.y = FLOOR_Y_WORLD + RADIUS_WORLD
            e.velocity.y = -e.velocity.y * BOUNCE_DAMPING
            e._prev_accel = e.compute_total_acceleration()
        # keep balls from drifting off-screen sideways forever
        if e.position.x < 0:
            e.position.x = 0
            e.velocity.x = -e.velocity.x * BOUNCE_DAMPING
        max_x = WIDTH / PPU
        if e.position.x > max_x:
            e.position.x = max_x
            e.velocity.x = -e.velocity.x * BOUNCE_DAMPING


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("pydamics -- click to drop balls")
    clock = pygame.time.Clock()

    world = World()
    world.on_step = bounce_check

    # a few balls to start
    for i in range(3):
        make_ball(world, 2.0 + i * 1.5, 10.0 + i * 2.0)

    # physics runs on its own thread; pygame just renders whatever
    # positions exist right now each frame
    world.run(dt=1 / 120, real_time=True)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                x_world = screen_to_world_x(mx)
                y_world = (HEIGHT - my) / PPU
                make_ball(world, x_world, y_world)

        screen.fill((245, 245, 245))
        pygame.draw.line(screen, (20, 20, 20), (0, HEIGHT - int(FLOOR_Y_WORLD * PPU)),
                          (WIDTH, HEIGHT - int(FLOOR_Y_WORLD * PPU)), 3)

        for e in world.entities:
            sx, sy = world_to_screen(e.position)
            pygame.draw.circle(screen, e.color, (sx, sy), RADIUS_PX)

        pygame.display.flip()
        clock.tick(60)

    world.stop()
    pygame.quit()


if __name__ == "__main__":
    main()
