import random

import pygame
import pygame.locals as pg
from pygame.event import Event

from pygskin import imgui
from pygskin.game import run_game
from pygskin.imgui import label

ROWS, COLS = 160, 160
CELL_WIDTH, CELL_HEIGHT = 5, 5

GOSPER_GUN = (
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

gui = imgui.IMGUI()
state = {
    "paused": True,
    "painting": False,
    "generation": 0,
}
cells: list[list[int]] = [[0] * COLS for _ in range(ROWS)]


def life(surface: pygame.Surface, events: list[Event], quit) -> None:
    surface.fill("black")

    for event in events:
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                quit()

            if event.key == pg.K_r:
                for y in range(ROWS):
                    for x in range(COLS):
                        cells[y][x] = random.choice((0, 1))

            if event.key == pg.K_c:
                cells[:] = [[0] * COLS for _ in range(ROWS)]
                state["generation"] = 0

            if event.key == pg.K_p:
                state["paused"] = not state["paused"]

            if event.key == pg.K_g:
                for y, row_ in enumerate(GOSPER_GUN):
                    for x, cell_ in enumerate(row_):
                        cells[y + 40][x + 40] = cell_ == "O"

        if event.type in (pg.MOUSEBUTTONDOWN, pg.MOUSEBUTTONUP):
            if state["paused"]:
                state["painting"] = not state["painting"]

        if event.type == pg.MOUSEMOTION and state["painting"]:
            x, y = event.pos
            cells[y // CELL_HEIGHT][x // CELL_WIDTH] = True

    if not state["paused"]:
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
        cells[:] = next_gen
        state["generation"] += 1

    for y, row in enumerate(cells):
        for x, cell in enumerate(row):
            if cell:
                pygame.draw.rect(
                    surface,
                    "white",
                    (x * CELL_WIDTH, y * CELL_HEIGHT, CELL_WIDTH, CELL_HEIGHT),
                )

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

if __name__ == "__main__":
    run_game(
        pygame.Window("Conway's Life", (800, 800)),
        life,
    )
