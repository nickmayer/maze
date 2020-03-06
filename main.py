#!/usr/bin/python3
import sys

from maze import AbsoluteDirection
from mazerunner import Algorithm
from mazerunner import MazeRunner, Runner, Direction


def ask_the_user(runner: Runner) -> Direction:
  return runner.ask_absolute()


def confuse_the_user(runner: Runner) -> Direction:
  return runner.ask_relative()


class AlgorithmWithAPast:
  what_step_is_it: int = 0

  def i_know_the_way(self, runner: Runner) -> Direction:
    """
    I know the way (as long as you pick a size of 15x15 and seed of 19790122)
    """
    U = AbsoluteDirection.UP
    R = AbsoluteDirection.RIGHT
    D = AbsoluteDirection.DOWN
    the_way = [U, U, R, R, U, R, R, R, R, R, R, U,
               R, R, U, U, R, R, D, R, R, U, U]

    next_move = the_way[self.what_step_is_it]
    self.what_step_is_it += 1
    return next_move

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

  choices = [
      ('Keyboard movement (absolute)', ask_the_user),
      ('Keyboard movement (relative)', confuse_the_user),
      ('I know the way!', AlgorithmWithAPast().i_know_the_way)
  ]
  print("Algorithms: ")
  for num, c in enumerate(choices):
    print(f'  {num}: {c[0]}')
  choice: str = input('Chose a algorithm: ')

  algorithm: Algorithm = lambda runner: AbsoluteDirection.NONE
  try:
    if len(choice) == 0:
      algo_index = 0
    else:
      algo_index = int(choice)
    algorithm = choices[algo_index][1]
  except (IndexError, ValueError):
    print(f'Invalid choice "{choice}"')
    exit(-1)

  try:
    maze.run(algorithm)
  except KeyboardInterrupt:
    exit(1)
