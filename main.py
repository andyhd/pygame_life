import random

import pygame
import pygame.locals as pg
from pygame.event import Event

from pygskin import imgui
from pygskin.game import run_game
from pygskin.imgui import label

ROWS, COLS = 160, 160
CELL_WIDTH, CELL_HEIGHT = 5, 5


def get_update_world_fn(state: dict):
    cells: list[list[int]] = [[0] * COLS for _ in range(ROWS)]

    def next_generation() -> list[list[int]]:
        next_gen = []
        for y in range(ROWS):
            row: list[int] = []
            curr_row = cells[y]
            prev_row = cells[(y - 1) % ROWS]
            next_row = cells[(y + 1) % ROWS]
            for x in range(COLS):
                alive = curr_row[x]
                prev_col = (x - 1) % COLS
                next_col = (x + 1) % COLS
                num_neighbours = (
                    prev_row[prev_col]
                    + prev_row[x]
                    + prev_row[next_col]
                    + curr_row[prev_col]
                    + curr_row[next_col]
                    + next_row[prev_col]
                    + next_row[x]
                    + next_row[next_col]
                )
                row.append(
                    (alive and 2 <= num_neighbours <= 3)
                    or (not alive and num_neighbours == 3)
                )
            next_gen.append(row)
        return next_gen

    def randomize() -> None:
        for y in range(ROWS):
            for x in range(COLS):
                cells[y][x] = random.choice((True, False))

    def gosper_gun() -> None:
        gun = (
            "......................................",
            ".........................O............",
            ".......................O.O............",
            ".............OO......OO............OO.",
            "............O...O....OO............OO.",
            ".OO........O.....O...OO...............",
            ".OO........O...O.OO....O.O............",
            "...........O.....O.......O............",
            "............O...O.....................",
            ".............OO.......................",
            "......................................",
        )
        for y, row in enumerate(gun):
            for x, cell in enumerate(row):
                cells[y + 40][x + 40] = cell == "O"

    def update_world(surface: pygame.Surface, events: list[Event]) -> None:
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    pygame.event.post(pygame.event.Event(pg.QUIT))

                if event.key == pg.K_r:
                    randomize()

                if event.key == pg.K_c:
                    cells[:] = [[0] * COLS for _ in range(ROWS)]
                    state["generation"] = 0

                if event.key == pg.K_p:
                    state["paused"] = not state["paused"]

                if event.key == pg.K_g:
                    gosper_gun()

            if event.type in (pg.MOUSEBUTTONDOWN, pg.MOUSEBUTTONUP):
                if state["paused"]:
                    state["painting"] = not state["painting"]

            if event.type == pg.MOUSEMOTION and state["painting"]:
                x, y = event.pos
                cells[y // CELL_HEIGHT][x // CELL_WIDTH] = True

        if not state["paused"]:
            cells[:] = next_generation()
            state["generation"] += 1

        surface.fill("black")
        for y, row in enumerate(cells):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(
                        surface,
                        "white",
                        (x * CELL_WIDTH, y * CELL_HEIGHT, CELL_WIDTH, CELL_HEIGHT),
                    )

    return update_world


def life():
    state = {
        "paused": True,
        "painting": False,
        "generation": 0,
    }
    update_world = get_update_world_fn(state)
    gui = imgui.IMGUI()

    def main_loop(window: pygame.Window, events: list[Event], _) -> None:
        surface = window.get_surface()

        update_world(surface, events)

        rect = surface.get_rect()
        with imgui.render(gui, surface) as render:
            render(
                label(f"Generation: {state['generation']}"),
                topleft=(30, 10),
            )
            if state["paused"]:
                render(
                    label(
                        "PAUSED\n"
                        "\n"
                        "P   - Toggle pause\n"
                        "R   - Randomise world\n"
                        "G   - Add a Gosper Gun\n"
                        "C   - Clear world\n"
                        "Esc - Quit\n"
                        "\n"
                        "While paused, you can draw\n"
                        "with the mouse"
                    ),
                    center=rect.center,
                )

    return main_loop


if __name__ == "__main__":
    run_game(
        pygame.Window("Conway's Life", (800, 800)),
        life(),
    )
