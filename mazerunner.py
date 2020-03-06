# -*- coding: utf-8 -*-
from __future__ import annotations

import curses
import random
import time
from itertools import tee
from typing import Callable, List

from maze import Direction, AbsoluteDirection, RelativeDirection, Maze, Point


class Runner:
  def can_move(self, direction: Direction) -> bool:
    """
    Returns True if there are no walls blocking movement in the given direction.
    Watch out, if you move in a direction that isn't allowed the high-voltage
    walls will zap you!
    """
    pass

  def heading(self) -> AbsoluteDirection:
    """Returns the current heading (direction the runner is facing)"""
    pass

  def ask_relative(self) -> RelativeDirection:
    """
    Prompts the user which direction they want to go, relative to the current
    heading. Use the arrow keys or "wasd" to select a direction. Pressing ESC or
    q will raise an exception.
    """
    pass

  def ask_absolute(self) -> AbsoluteDirection:
    """
    Prompts the user which direction they want to go, in absolute terms. Use the
    arrow keys or "wasd" to select a direction. Pressing ESC or q will raise an
    exception.
    """
    pass

  def clone(self, direction: Direction, name: str = None) -> None:
    """
    Make a clone of yourself, pointing in the given direction. Will set the
    born at position.

    Note: if you attempt to clone your self to have more copies of you than
    there are in the maze, a black hole is formed and sucks the maze into a
    singularity.
    """
    pass

  def history(self) -> List[Point]:
    """
    Returns a list of all points this runner has visited, from first to current.
    """
    pass

  def relative_history(self) -> List[RelativeDirection]:
    """
    Returns a list of all directions this runner took, from first to current.
    """
    pass

  def name(self) -> str:
    """What is this runner's name?"""
    pass

  def born_at(self) -> Point:
    """
    Returns where this runner first came into existence. Will be None for the
    initial runner.
    """
    pass

  def age(self) -> int:
    """
    Returns how long since this runner came into existence. Can be used along
    with history() to see what has been done since the point at which the runner
    was born.
    If age() > len(history()) congratulations! that means this runner is the
    very first runner to ever exist, and as far as we can tell has always
    existed (has a born_at() of None!)
    """
    pass


# This is the type needed when creating a new runner. The Algorithm must be
#  given when calling the MazeRunner.run method, as it determines what path will
#  be taken. If you return a direction that results in walking into one of the
#  electrified walls the Runner will be vaporized and will no longer exist in
#  the maze.
Algorithm = Callable[[Runner], Direction]


class MazeRunner:
  """Curses based console maze runner"""
  maze: Maze
  _delay_time: float
  _runners: List[_RunnerImpl] = []
  _crashed: List[_RunnerImpl] = []

  def __init__(self,
               width,
               height,
               maze_seed=None,
               delay_time=0.1):
    self._delay_time = delay_time
    print("Creating the Maze ({w}x{h} seed={s})".format(w=width,
                                                        h=height,
                                                        s=maze_seed))
    time.sleep(1)
    r = random.Random()
    r.seed(maze_seed, version=1)
    self.maze = Maze(width, height, r)

  def clone_runner(self,
                   runner: _RunnerImpl,
                   direction: Direction,
                   name: str):
    if len(self._runners) > self.maze.height * self.maze.width:
      raise Exception(f"Not allowed to have more runners ({len(self._runners)})"
                      f" than cells in the maze"
                      f" ({self.maze.height * self.maze.width})!")
    self._runners.append(runner.duplicate(direction, name))

  def run(self, algorithm: Algorithm):
    """Run the maze. Returns true if it was solved"""
    curses.wrapper(lambda stdscr: self._run(stdscr, algorithm))

  def _run(self, screen, algorithm: Callable[[Runner], Direction]):
    screen.clear()
    screen.refresh()

    self._runners.append(_RunnerImpl(self, self.maze.start, screen))

    # Setup the colors we're going to use
    curses.start_color()
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)

    # No need to regenerate the maze every time, it never changes. Figure out
    # the max dimensions and allocate a curses pad for drawing the maze
    maze_lines: str = str(self.maze)
    maze_char_h: int = len(maze_lines.split('\n')) + 1
    maze_char_w: int = max([len(x) for x in maze_lines.split('\n')])

    # turn off input echoing, disable the cursor, etc
    curses.noecho()
    curses.curs_set(0)
    curses.cbreak()

    # Create screen for the maze
    maze_screen = curses.newwin(maze_char_h, maze_char_w + 1, 0, 0)
    maze_screen.bkgd(' ', curses.color_pair(1))

    # Create screen for the status field
    status_screen = curses.newwin(6, maze_char_w - 2, maze_char_h, 1)
    status_screen.bkgd(' ', curses.color_pair(3))
    status_screen.box()

    # Loop where on character input
    winner = None
    loop_count: int = 0
    total_time = 0
    while True:
      screen.refresh()

      # Draw the maze and runners
      maze_screen.clear()
      maze_screen.addstr(0, 0, maze_lines)
      for runner in self._runners:
        p: Point = runner.char_position()
        maze_screen.addstr(p.y, p.x, runner.display())
      for runner in self._crashed:
        p: Point = runner.char_position()
        maze_screen.addstr(p.y, p.x, runner.display(), curses.color_pair(2))
      maze_screen.refresh()

      # Draw the status area
      status_screen.clear()
      blink = False
      if winner:
        status = f'You won in {loop_count} moves.'
        blink = True
      elif not self._runners:
        status = f'You crashed into a wall after {loop_count} moves.'
        blink = True
      else:
        status = f'{loop_count} steps taken'

      if winner or len(self._runners) == 1:
        r = winner or self._runners[0]
        absolute = ' '.join([str(d) for d in r.absolute_history()])
        relative = ' '.join([str(d) for d in r.relative_history()])
        status_screen.addstr(3, 2, absolute[0:maze_char_w-1])
        status_screen.addstr(4, 2, relative[0:maze_char_w-1])

      status_screen.addstr(1, 2, status, curses.A_BLINK if blink else 0)
      time_status = f'{total_time:.5f} seconds elapsed.'
      status_screen.addstr(2, 2, time_status, curses.A_BLINK if blink else 0)
      status_screen.refresh()

      # If we found our winner, pause until a key is pressed then quit.
      if winner or not self._runners:
        screen.getch()
        break

      # Use the given algorithm to advance the paths
      loop_count += 1
      start_time = time.time()
      i: int = 0
      while i < len(self._runners):
        # Since the algorithm can ask a runner to duplicate itself, we need
        # to iterate until we hit the end of the list, even if the size of
        # the list is growing during the iteration.
        runner = self._runners[i]

        direction = algorithm(runner)
        moved = runner.move(direction)
        if not moved:
          # If we gave a command that didn't result in a move, we consider the
          # runner dead and remove it.
          self._crashed.append(self._runners[i])
          del self._runners[i]
          continue
        i += 1

        if runner.position == self.maze.end:
            winner = runner
            break
      end_time = time.time()
      elapsed = end_time - start_time
      total_time += elapsed
      if elapsed < self._delay_time:
        time.sleep(self._delay_time - elapsed)


class _RunnerImpl(Runner):
  """Data for a person running the maze"""
  position: Point
  _name: str = 'Runner0000'
  _parent: MazeRunner
  _heading: AbsoluteDirection
  _history: List[Point]
  _born_at_index: int = None

  def __init__(self, parent: MazeRunner, position: Point, screen):
    self.position = position
    self._history = []
    self.screen = screen
    # We always start on the left edge, so we know we're going right to start
    self._heading = AbsoluteDirection.RIGHT
    self._parent = parent

  def history(self) -> List[Point]:
    # It is important that list + list returns a copy so that the caller doesn't
    #  mistakenly rewrite the past, causing a paradox that could end existence!
    return self._history + [self.position]

  def absolute_history(self) -> List[AbsoluteDirection]:
    past_points = self.history()
    # Tee will make 2 streams from the iterable. We then advance end by 1
    start, end = tee(past_points)
    next(end, None)
    return [a.direction(b) for a, b in zip(start, end)]

  def relative_history(self) -> List[RelativeDirection]:
    absolute_directions = ([AbsoluteDirection.RIGHT] + self.absolute_history())
    start, end = tee(absolute_directions)
    next(end, None)
    return [a.relative(b) for a, b in zip(start, end)]

  def name(self) -> str:
    return self._name

  def born_at(self) -> Point:
    return ((self.history())[self._born_at_index]
            if self._born_at_index is not None
            else None)

  def age(self) -> int:
    return len(self._history) - (self._born_at_index
                                 if self._born_at_index is not None
                                 else -1)

  def clone(self, direction: Direction, name: str = None) -> None:
    self._parent.clone_runner(self, direction, name)

  def duplicate(self, direction: Direction, name: str = None) -> _RunnerImpl:
    global _clone_num
    if name is None:
      _clone_num += 1
      name = f'Runner{_clone_num:04d}'

    c = _RunnerImpl(self._parent, self.position, None)
    c._born_at_index = len(self._history)
    c._history = list(self._history)
    c._name = name
    c._heading = self._to_absolue(direction)
    return c

  def can_move(self, direction: Direction) -> bool:
    abs_direction: AbsoluteDirection = self._to_absolue(direction)
    return self._parent.maze.can_move(self.position, abs_direction)

  def heading(self) -> AbsoluteDirection:
    return self._heading

  def ask_relative(self) -> RelativeDirection:
    abs_dir = self.ask_absolute()
    if abs_dir == AbsoluteDirection.UP:
      return RelativeDirection.FORWARD
    elif abs_dir == AbsoluteDirection.DOWN:
      return RelativeDirection.BACKWARD
    elif abs_dir == AbsoluteDirection.LEFT:
      return RelativeDirection.LEFT
    elif abs_dir == AbsoluteDirection.RIGHT:
      return RelativeDirection.RIGHT
    return RelativeDirection.NONE

  def ask_absolute(self) -> AbsoluteDirection:
    c = self.screen.getch()
    direction = None
    while direction is None:
      if c == curses.KEY_UP or c == ord('w'):
        direction = AbsoluteDirection.UP
      elif c == curses.KEY_DOWN or c == ord('s'):
        direction = AbsoluteDirection.DOWN
      elif c == curses.KEY_LEFT or c == ord('a'):
        direction = AbsoluteDirection.LEFT
      elif c == curses.KEY_RIGHT or c == ord('d'):
        direction = AbsoluteDirection.RIGHT
      elif c == 27 or c == ord('q') or c == ord('Q'):
        raise KeyboardInterrupt("User Requested to Quit")
    return direction

  def char_position(self) -> Point:
    return Maze.char_position(self.position)

  def move(self, direction: Direction) -> bool:
    abs_direction: AbsoluteDirection = self._to_absolue(direction)
    self._heading = abs_direction
    if abs_direction != AbsoluteDirection.NONE and self.can_move(abs_direction):
      self._history.append(self.position)
      self.position = Maze.move(self.position, abs_direction)
      return True
    return False

  def _to_absolue(self, direction: Direction) -> AbsoluteDirection:
    if isinstance(direction, AbsoluteDirection):
      return direction
    elif isinstance(direction, RelativeDirection):
      return self.heading().absolute(direction)

    raise Exception(f"Unexpected direction {direction}")

  def _to_relative(self, direction: Direction) -> RelativeDirection:
    if isinstance(direction, RelativeDirection):
      return direction
    elif isinstance(direction, AbsoluteDirection):
      return self.heading().relative(direction)
    raise Exception(f"Unexpected direction {direction}")

  def display(self) -> str:
    return str(self.heading())


_clone_num = 0
