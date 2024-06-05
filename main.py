from __future__ import annotations

import random
from collections.abc import Iterator
from dataclasses import dataclass

import pygame
import pygame.locals as pg
from pygame.event import Event

from pygskin.clock import Clock
from pygskin.game import GameLoop
from pygskin.grid import Grid
from pygskin.text import Text
from pygskin.window import Window


@dataclass
class Cell:
    alive: bool
    num_neighbours: int


class CellGrid(Grid):
    def __post_init__(self) -> None:
        super().__post_init__()
        self.cells = self.empty()

    def __getitem__(self, xy: tuple[int, int]) -> Cell:
        x, y = xy
        return self.cells[y][x]

    def __setitem__(self, xy: tuple[int, int], value: Cell) -> None:
        x, y = xy
        self.cells[y][x] = value

    def empty(self) -> list[list[Cell]]:
        return [[Cell(False, 0) for x in range(self.cols)] for y in range(self.rows)]

    def with_keys(self) -> Iterator[tuple[tuple[int, int], Cell]]:
        for xy in self:
            yield xy, self[xy]

    def neighbours(self, xy) -> Iterator[Cell]:
        for xy in super().neighbours(*xy, wrap=True):
            yield self[xy]


class World(pygame.sprite.Sprite):
    def __init__(self, grid: Grid, cell_size: tuple[int, int]) -> None:
        pygame.sprite.Sprite.__init__(self)
        self.grid = grid
        self.grid.cell_size = cell_size
        self.rect = pygame.Rect((0, 0), grid.mapped_size)
        self.cells = CellGrid(*grid.size)
        self.surface = pygame.Surface(self.rect.size)
        self.image_generation = self.generation = 0

    def next_generation(self) -> None:
        next_gen = CellGrid(*self.grid.size)

        for xy, cell in self.cells.with_keys():
            alive = (cell.alive and 2 <= cell.num_neighbours <= 3) or (
                not cell.alive and cell.num_neighbours == 3
            )

            if alive:
                next_gen[xy].alive = alive
                # for neighbour in next_gen.neighbours(xy):
                #     neighbour.num_neighbours += 1
                x, y = xy
                rows = ((y - 1) % self.grid.rows, y, (y + 1) % self.grid.rows)
                cols = ((x - 1) % self.grid.cols, x, (x + 1) % self.grid.cols)
                for ny in rows:
                    for nx in cols:
                        if not (ny == y and nx == x):
                            next_gen[(nx, ny)].num_neighbours += 1

        self.cells = next_gen
        self.generation += 1

    def randomize(self) -> None:
        for _xy, cell in self.cells.with_keys():
            cell.alive = random.random() < 0.5

    def refresh(self) -> None:
        for xy, cell in self.cells.with_keys():
            cell.num_neighbours = sum(
                neighbour.alive for neighbour in self.cells.neighbours(xy)
            )
        self.image_generation = -1

    @property
    def image(self) -> pygame.Surface:
        if self.image_generation != self.generation:
            self.surface.fill("black")
            for xy, cell in self.cells.with_keys():
                if cell.alive:
                    pygame.draw.rect(self.surface, "white", self.grid.rect(xy))
            self.image_generation = self.generation
            label = Text(f"Generation: {self.generation}", background="black")
            label.image.set_alpha(196)
            label.rect.bottom = self.grid.mapped_size[1]
            self.surface.blit(label.image, label.rect)
        return self.surface


class Game(GameLoop):
    def setup(self) -> None:
        Window.rect.size = (800, 800)
        Window.title = "Conway's Life"

        self.world = World(Grid(160, 160), cell_size=(5, 5))

        self.state = {
            "paused": True,
            "painting": False,
            "world": self.world,
        }

        self.pause_label = Text(
            (
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
            background="blue",
            padding=(20, 20),
            center=Window.rect.center,
        )

    def update(self, events: list[Event]) -> None:
        Clock.tick()

        for event in events:
            if event.type == pg.QUIT:
                self.running = False

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.running = False

                if event.key == pg.K_r:
                    self.world.randomize()
                    self.world.refresh()

                if event.key == pg.K_c:
                    self.world.cells = CellGrid(*self.world.grid.size)
                    self.world.generation = 0

                if event.key == pg.K_p:
                    self.state["paused"] = not self.state["paused"]

                if event.key == pg.K_g:
                    self.gosper_gun()

            if event.type in (pg.MOUSEBUTTONDOWN, pg.MOUSEBUTTONUP):
                if self.state["paused"]:
                    self.state["painting"] = not self.state["painting"]

            if event.type == pg.MOUSEMOTION and self.state["painting"]:
                self.paint(event.pos)

        if any(event.type == pg.QUIT for event in events):
            self.running = False

        if not self.state["paused"]:
            self.world.next_generation()

    def draw(self) -> None:
        Window.surface.blit(self.world.image, self.world.rect)
        if self.state["paused"]:
            Window.surface.blit(self.pause_label.image, self.pause_label.rect)
        pygame.display.flip()

    def paint(self, pos: tuple[int, int]) -> None:
        x, y = pos
        cell_width, cell_height = self.world.grid.cell_size
        self.world.cells[(x // cell_width, y // cell_height)].alive = True
        self.world.refresh()

    def gosper_gun(self) -> None:
        cells = (
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
        for y, row in enumerate(cells):
            for x, cell in enumerate(row):
                self.world.cells[(x + 40, y + 40)].alive = cell == "O"
        self.world.refresh()


if __name__ == "__main__":
    Game().start()
