import curses
import random
import time
from typing import Callable, List

from maze import Direction, AbsoluteDirection, RelativeDirection, Maze, Point


class Runner:
  def can_move(self, direction: Direction) -> bool:
    """Returns True if there are no walls blocking movement in the given direction"""
    pass

  def heading(self) -> AbsoluteDirection:
    """Returns the current heading (direction the runner is facing)"""
    pass

  def ask_relative(self) -> RelativeDirection:
    """
    Prompts the user which direction they want to go, relative to the current heading.
    Use the arrow keys or "wasd" to select a direction. Pressing ESC or q will raise
    an exception.
    """
    pass

  def ask_absolute(self) -> AbsoluteDirection:
    """
    Prompts the user which direction they want to go, in absolute terms. Use the arrow keys
    or "wasd" to select a direction. Pressing ESC or q will raise an exception.
    """
    pass


# This is the type needed when creating a new runner. The Algorithm must be given when
# calling the MazeRunner.run method, as it determines what path will be taken.
Algorithm = Callable[[Runner], Direction]


class MazeRunner:
  """Curses based console maze runner"""
  _maze: Maze
  _delay_time: float

  def __init__(self, width, height, maze_seed=None, walk_seed=None, seed=None, delay_time=0.1):
    self._delay_time = delay_time
    if seed is not None:
      maze_seed = maze_seed if maze_seed is not None else seed
      walk_seed = walk_seed if walk_seed is not None else seed

    print("Creating the Maze ({w}x{h} seed={s})".format(w=width,
                                                        h=height,
                                                        s=maze_seed))
    time.sleep(1)
    random.seed(maze_seed)
    self._maze = Maze(width, height)
    random.seed(walk_seed)

  def run(self, algorithm: Algorithm):
    """Run the maze. Returns true if it was solved"""
    curses.wrapper(lambda stdscr: self._run(stdscr, algorithm))

  def _run(self, screen, algorithm: Callable[[Runner], Direction]):
    screen.clear()
    screen.refresh()

    self.runners = [_RunnerImpl(self, self._maze.start, screen)]

    # Setup the colors we're going to use
    curses.start_color()
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)

    # No need to regenerate the maze every time, it never changes. Figure out
    # the max dimensions and allocate a curses pad for drawing the maze
    maze_lines: str = str(self._maze)
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
    status_screen = curses.newwin(3, maze_char_w - 2, maze_char_h, 1)
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
      for runner in self.runners:
        p: Point = runner.char_position()
        maze_screen.addstr(p.y, p.x, runner.display())
      maze_screen.refresh()

      # Draw the status area
      status_screen.clear()
      if not winner:
        status = f'{loop_count} steps taken'
      else:
        status = f'You won in {loop_count} moves. ' \
                 f'It took {total_time:.2f} seconds.'
      status_screen.addstr(1, 2, status, curses.A_BLINK if winner else 0)
      status_screen.refresh()

      # If we found our winner, pause until a key is pressed then quit.
      if winner:
        screen.getch()
        break

      # Use the given algorithm to advance the paths
      loop_count += 1
      start_time = time.time()
      i: int = 0
      while i < len(self.runners):
        # Since the algorithm can ask a runner to duplicate itself, we need
        # to iterate until we hit the end of the list, even if the size of
        # the list is growing during the iteration.
        runner = self.runners[i]
        i += 1

        direction = algorithm(runner)
        runner.move(direction)
        if runner.position == self._maze.end:
          winner = runner
          break
      end_time = time.time()
      elapsed = end_time - start_time
      total_time += elapsed
      if elapsed < self._delay_time:
        time.sleep(self._delay_time - elapsed)


class _RunnerImpl(Runner):
  """Data for a person running the maze"""
  parent: MazeRunner
  position: Point
  history: List[Point]

  def __init__(self, parent: MazeRunner, position: Point, screen):
    self.parent = parent
    self.position = position
    self.history = []
    self.screen = screen

  def can_move(self, direction: Direction) -> bool:
    abs_direction: AbsoluteDirection = self._to_absolue(direction)
    return self.parent._maze.can_move(self.position, abs_direction)

  def heading(self) -> AbsoluteDirection:
    if not self.history:
      # We always start on the left edge, so we know we're going right to start
      return AbsoluteDirection.RIGHT
    else:
      return Maze.heading(self.history[-1], self.position)

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

  def move(self, direction: Direction) -> None:
    direction = self._to_absolue(direction)
    if self.can_move(direction):
      self.history.append(self.position)
      self.position = Maze.move(self.position, direction)

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
    h = {
      AbsoluteDirection.UP: '▲',
      AbsoluteDirection.DOWN: '▼',
      AbsoluteDirection.LEFT: '◀',
      AbsoluteDirection.RIGHT: '▶'
    }
    return h.get(self.heading(), '@')

