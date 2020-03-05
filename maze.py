# -*- coding: utf-8 -*-
import random
from dataclasses import dataclass
from dataclasses import field
from typing import Dict
from typing import Iterable
from typing import Set


@dataclass(frozen=True)
class Point:
  """Represents a 2d position in the maze"""
  x: int
  y: int


class Maze(object):
  """Represents a two dimensional maze"""
  width: int
  height: int
  start: Point

  def __init__(self, width=20, height=10):
    """
    Creates a new maze with the given sizes, with all walls standing.
    """
    self.width = width
    self.height = height
    self.start = Point(0, random.randrange(0, height))
    self._create_maze()

  @dataclass
  class _Cell:
    """Represents a cell in the maze"""
    position: Point
    connections: Set[Point] = field(default_factory=set)

    def connect(self, connect_to):
      self.connections.add(connect_to)

  class _Cells(dict):
    """
    Custom dictionary that will automatically create a new cell at the given
    position with no connections
    """
    def __missing__(self, key):
      c = Maze._Cell(key)
      self[key] = c
      return c

  _cells: Dict[Point, _Cell] = _Cells()

  def _create_maze(self):
    """
    Randomized Prim's algorithm - Modified version (Taken from
    https://en.wikipedia.org/wiki/Maze_generation_algorithm)

    This algorithm is a randomized version of Prim's algorithm.

    1.) Start with a grid full of walls.
    2.) Pick a cell, mark it as part of the maze. Add the walls of the cell to
        the wall list.
    3.) While there are walls in the list:
      a.) Pick a random wall from the list. If only one of the two cells that
          the wall divides is visited, then:
        i.) Make the wall a passage and mark the unvisited cell as part of the
            maze.
        ii.) Add the neighboring walls of the cell to the wall list.
      b.) Remove the wall from the list.

    Although the classical Prim's algorithm keeps a list of edges, for maze
    generation we could instead maintain a list of adjacent cells. If the
    randomly chosen cell has multiple edges that connect it to the existing
    maze, select one of these edges at random. This will tend to branch slightly
    more than the edge-based version above.

    Example representation of 3x3 maze with all cells having a wall:
          0   1   2
        ┌───┬───┬───┐
      0 │   │   │   │
        ├───┼───┼───┤
      1 │   │   │   │
        ├───┼───┼───┤
      2 │   │   │   │
        └───┴───┴───┘
    """

    def get_adjacent_points(pt: Point) -> Iterable[Point]:
      """Return valid adjacent points that are NOT part of the maze"""
      if pt.x > 0:
        yield Point(pt.x - 1, pt.y)
      if pt.x + 1 < self.width:
        yield Point(pt.x + 1, pt.y)
      if pt.y > 0:
        yield Point(pt.x, pt.y - 1)
      if pt.y + 1 < self.height:
        yield Point(pt.x, pt.y + 1)

    # Initialize the cells to a default dict, which will ensure that all
    # requested cells will be initialized to having no connections (has 4 walls)
    # and add the start cell to the dictionary
    _ = self._cells[self.start]
    adj_cells: Set[Point]
    adj_cells = set(get_adjacent_points(self.start))

    while len(adj_cells) > 0:
      # Pick a random cell from the remaining adjacencies
      cell = random.sample(adj_cells, 1)[0]
      adj_cells.remove(cell)

      # Chose a random wall that connects to the maze, and remove it
      adj = set(get_adjacent_points(cell))
      connections = [p for p in adj if p in self._cells]
      connect_to = random.choice(connections)
      self._cells[cell].connect(connect_to)
      self._cells[connect_to].connect(cell)

      # Add all of the adjacent points to this new cell that aren't in the maze
      non_connections = {p for p in adj if p not in self._cells}
      adj_cells |= non_connections
