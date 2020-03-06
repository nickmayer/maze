#!/usr/bin/python3
import sys
from mazerunner import MazeRunner, Runner, Direction


def ask_the_user(runner: Runner) -> Direction:
  return runner.ask_absolute()


if __name__ == '__main__':
  if len(sys.argv) > 1:
    width = int(sys.argv[1])
    if len(sys.argv) > 2:
      height = int(sys.argv[2])
    else:
      height = width
  else:
    width = 15
    height = 15

  if len(sys.argv) > 3:
    maze_seed = int(sys.argv[3])
  else:
    maze_seed = 19790122

  maze = MazeRunner(width, height, maze_seed=maze_seed)
  try:
    maze.run(ask_the_user)
  except KeyboardInterrupt:
    exit(1)
