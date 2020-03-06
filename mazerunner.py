import curses
import random
import time
from typing import Callable, List

from maze import Direction, AbsoluteDirection, RelativeDirection, Maze, Point


class Runner:
  def can_move(self, direction: Direction):
    pass

  def ask_relative(self) -> RelativeDirection:
    pass

  def ask_absolute(self) -> AbsoluteDirection:
    pass

  def name(self) -> str:
    pass


class _RunnerImpl(Runner):
  """Data for a person running the maze"""
  maze: Maze
  position: Point
  symbol: str
  history: List[Point]

  def __init__(self, maze: Maze, position: Point, screen):
    self.maze = maze
    self.position = position
    self.history = []
    self.symbol = '@'
    self.screen = screen

  def can_move(self, direction: Direction):
    return self.maze.can_move(self.position, direction)

  def ask_absolute(self) -> AbsoluteDirection:
    c = self.screen.getch()
    direction = None
    while direction == None:
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

  def char_position(self):
    return Maze.char_position(self.position)

  def move(self, direction):
    if self.can_move(direction):
      self.history.append(self.position)
      self.position = Maze.move(self.position, direction)


class MazeRunner:
  """Curses based console maze runner"""
  maze: Maze
  delay_time: float = 0.1

  def __init__(self, width, height, maze_seed=None, walk_seed=None, seed=None):
    if seed is not None:
      maze_seed = maze_seed if maze_seed is not None else seed
      walk_seed = walk_seed if walk_seed is not None else seed

    print("Creating the Maze ({w}x{h} seed={s})".format(w=width,
                                                        h=height,
                                                        s=maze_seed))
    time.sleep(1)
    random.seed(maze_seed)
    self.maze = Maze(width, height)
    random.seed(walk_seed)

  def run(self, algorithm: Callable[[Runner], Direction]):
    """Run the maze. Returns true if it was solved"""
    curses.wrapper(lambda stdscr: self._run(stdscr, algorithm))

  def _run(self, screen, algorithm: Callable[[Runner], Direction]):
    screen.clear()
    screen.refresh()

    self.runners = [_RunnerImpl(self.maze, self.maze.start, screen)]

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
        maze_screen.addstr(p.y, p.x, runner.symbol)
      maze_screen.refresh()

      # Draw the status area
      status_screen.clear()
      if not winner:
        status = f'{loop_count} steps taken'
      else:
        status = f'You won in {loop_count} moves. It took {total_time:.2f} seconds.'
      status_screen.addstr(1, 2, status, curses.A_BLINK if winner else 0)
      status_screen.refresh()

      # If we found our winner, pause until a key is pressed then quit.
      if winner:
        screen.getch()
        break

      # Use the given algorithm to advance the paths
      loop_count += 1
      start_time = time.time()
      for runner in self.runners:
        direction = algorithm(runner)
        runner.move(direction)
        if runner.position == self.maze.end:
          winner = runner
          break
      end_time = time.time()
      elapsed = end_time - start_time
      total_time += elapsed
      if elapsed < self.delay_time:
        time.sleep(self.delay_time - elapsed)
