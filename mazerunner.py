import curses
import random
import time

from maze import Maze


class MazeRunner:
  """Curses based console maze runner"""
  maze: Maze

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

  def run(self) -> bool:
    """Run the maze. Returns true if it was solved"""
    return curses.wrapper(lambda stdscr: self._run(stdscr))

  def _run(self, screen) -> bool:
    # No need to regenerate the maze every time, it never changes. Figure out
    # the max dimensions and allocate a curses pad for drawing the maze
    maze_lines: str = str(self.maze)
    maze_char_h: int = len(maze_lines.split('\n')) + 1
    maze_char_w: int = max([len(x) for x in maze_lines.split('\n')]) + 1

    # turn off input echoing, disable the cursor
    curses.noecho()
    curses.curs_set(0)
    # respond to keys immediately (don't wait for enter)
    curses.cbreak()

    # Create screens for the maze and status field
    maze_screen = curses.newwin(maze_char_h, maze_char_w, 0, 0)
    status_screen = curses.newwin(2, maze_char_w, maze_char_h, 0)

    # Loop where on character input
    status = ''
    while True:
      maze_screen.clear()
      maze_screen.addstr(0, 0, maze_lines)
      maze_screen.refresh()

      status_screen.clear()
      status_screen.addstr(0, 5, status)
      status_screen.refresh()

      c = screen.getch()
      if c == curses.KEY_UP:
        status = '⯅'
      elif c == curses.KEY_DOWN:
        status = '⯆'
      elif c == curses.KEY_LEFT:
        status = '⯇'
      elif c == curses.KEY_RIGHT:
        status = '⯈'
      elif c == 27 or c == ord('q') or c == ord('Q'):
        # 27 is ESC, doesn't have a constant
        break
      else:
        status = 'Key {} {} {}'.format(c, curses.unctrl(c), curses.keyname(c))

    return False
