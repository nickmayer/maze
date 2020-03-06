# -*- coding: utf-8 -*-
from __future__ import annotations

import random
from dataclasses import dataclass
from dataclasses import field
from enum import Enum, unique, auto
from typing import Dict, Union
from typing import Iterable
from typing import List
from typing import Set


@unique
class RelativeDirection(Enum):
  NONE = auto()
  FORWARD = auto()
  BACKWARD = auto()
  LEFT = auto()
  RIGHT = auto()


@unique
class AbsoluteDirection(Enum):
  NONE = auto()
  UP = auto()
  DOWN = auto()
  LEFT = auto()
  RIGHT = auto()


# Generic direction can be either relative (up, down, etc.) or cardinal (north, south, etc.)
Direction = Union[RelativeDirection, AbsoluteDirection]


@dataclass(order=True, frozen=True)
class Point:
  """Represents a 2d position in the maze"""
  x: int
  y: int

  def __repr__(self):
    return f'({self.x}, {self.y})'

  def above(self) -> Point:
    return Point(self.x, self.y - 1)

  def below(self) -> Point:
    return Point(self.x, self.y + 1)

  def left(self) -> Point:
    return Point(self.x - 1, self.y)

  def right(self) -> Point:
    return Point(self.x + 1, self.y)


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
    self.end = Point(width - 1, random.randrange(0, height))
    self._create_maze()

  @staticmethod
  def char_position(position: Point) -> Point:
    return Point(position.x * 4 + 2, position.y * 2 + 1)

  def can_move(self, position: Point, direction: Direction):
    target = self.move(position, direction)
    return self._cells[position].connected_to(target)

  @staticmethod
  def move(position: Point, direction: Direction):
    # TODO: Convert relative to absolute first

    if direction == AbsoluteDirection.NONE:
      return position
    elif direction == AbsoluteDirection.UP:
      return position.above()
    elif direction == AbsoluteDirection.DOWN:
      return position.below()
    elif direction == AbsoluteDirection.LEFT:
      return position.left()
    elif direction == AbsoluteDirection.RIGHT:
      return position.right()

    raise Exception(f"Unexpected direction {direction}")

  @dataclass
  class _Cell:
    """Represents a cell in the maze"""
    _position: Point
    _connections: Set[Point] = field(default_factory=set)

    def connect(self, connect_to):
      self._connections.add(connect_to)

    def wall_above(self):
      return self._position.above() not in self._connections

    def wall_below(self):
      return self._position.below() not in self._connections

    def wall_left(self):
      return self._position.left() not in self._connections

    def wall_right(self):
      return self._position.right() not in self._connections

    def connected(self) -> bool:
      if self._connections:
        return True
      else:
        return False

    def connected_to(self, target: Point):
      return target in self._connections

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
    adj_cells: Set[Point]
    adj_cells = set(get_adjacent_points(self.start))

    while len(adj_cells) > 0:
      # Pick a random cell from the remaining adjacencies
      cell = random.sample(adj_cells, 1)[0]
      adj_cells.remove(cell)

      # Chose a random wall that connects to the maze, and remove it
      adj = set(get_adjacent_points(cell))
      connections = [p for p in adj if (p == self.start or
                                        self._cells[p].connected())]
      connect_to = random.choice(connections)
      self._cells[cell].connect(connect_to)
      self._cells[connect_to].connect(cell)

      # Add all of the adjacent points to this new cell that aren't in the maze
      non_connections = {p for p in adj if not self._cells[p].connected()}
      adj_cells |= non_connections

  def __str__(self):
    """
    This will print the text representation of a single cell.

    The example shows which characters belong to cell (1,1). The characters
    also need to access the cell to the left and above to determine the proper
    corner character 'C'
          0   1   2
        ┌───┬───┬───┐
      0 │   │   │   │      N
        ├───CXXX┼───┤    W─┼─E
      1 │   Y␣$␣|   │      S
        ├───┼───┼───┤
      2 │   │   │   │
        └───┴───┴───┘
    """
    # For different draw styles:
    #  https://en.wikipedia.org/wiki/Box-drawing_character
    #  http://www.fileformat.info/info/unicode/block/box_drawing/list.htm
    d = {
        'SENW': '┼',
        'SEN': '├', 'ENW': '┴', 'SNW': '┤', 'SEW': '┬',
        'EN': '└', 'NW': '┘', 'SE': '┌', 'SW': '┐',
        'SN': '│', 'N': '╵', 'S': '╷',
        'EW': '─', 'W': '╴', 'E': '╶'
    }

    def get_corner(p: Point) -> str:
      cell = self._cells[p]
      corner_description: str = ""
      if cell.wall_left():
        corner_description += 'S'
      if cell.wall_above():
        corner_description += 'E'
      try:
        if self._cells.get(Point(p.x, p.y - 1)).wall_left():
          corner_description += 'N'
      except AttributeError:
        pass
      try:
        if self._cells.get(Point(p.x - 1, p.y)).wall_above():
          corner_description += 'W'
      except AttributeError:
        pass
      return d.get(corner_description, '⚠')

    lines: List[str] = []
    for y in range(0, self.height):
      line1: str = ''
      line2: str = ''
      for x in range(0, self.width):
        p = Point(x, y)
        cell = self._cells[p]
        line1 += get_corner(p) + (d['EW'] * 3 if cell.wall_above() else '   ')
        line2 += d['SN'] + '   ' if (cell.wall_left()
                                     and not p == self.start) else '    '
      if y == 0:
        line1 += d['SW']
      elif self._cells[Point(self.width - 1, y)].wall_above():
        line1 += d['SNW']
      else:
        line1 += d['SN']
      line2 += d['SN'] if y != self.end.y else ' '
      lines.append(line1)
      lines.append(line2)

    # The bottom line has to look at the bottom row to decide if there is a wall
    #  going up to connect.
    bottom = d['EN'] + d['EW'] * 3
    for x in range(1, self.width):
      p = Point(x, self.height - 1)
      bottom += ((d['ENW'] if self._cells[p].wall_left() else d['EW'])
                 + (d['EW'] * 3))
    bottom += d['NW']

    lines.append(bottom)
    return '\n'.join(lines)

