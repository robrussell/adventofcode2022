
from dataclasses import dataclass
from dataclasses import field
from typing import Callable
from typing import List
from typing import Optional

MonkeyId = str
WorryItemId = str
WorryOperation = Callable

@dataclass
class WorryItem:
  id : WorryItemId
  worry_level : int

class Monkey:
  def __init__(self, id : MonkeyId, 
      starting_items : List[WorryItem],
      operation : WorryOperation,
      test_division : int,
      branch_true : MonkeyId,
      branch_false : MonkeyId):
    self.id_ : MonkeyId = id
    self.items_ : List[WorryItem] = starting_items
    self.operation_ : WorryOperation = operation
    self.test_division_ : int = test_division
    self.branch_true_ : MonkeyId = branch_true
    self.branch_false_ : MonkeyId = branch_false

@dataclass
class MonkeyBuilder:
    # Identifier from input file
    id : MonkeyId
    # List of worry items from input file
    starting_items : Optional[List[WorryItem]] = field(init=False)
    # Math operation interpretted as a function
    operation : Optional[WorryOperation] = field(init=False)
    # Number to use in division test
    test_division : Optional[int] = field(init=False)
    # ID of monkey to throw item to on True result
    branch_true : Optional[MonkeyId] = field(init=False)
    # ID of monkey to throw item to on False result
    branch_false : Optional[MonkeyId] = field(init=False)

    def build(self) -> Monkey:
      if not (self.operation and 
        self.starting_items and 
        self.test_division and 
        self.branch_true and
        self.branch_false):
        raise Exception('Incomplete monkey.')
      return Monkey(self.id, 
        self.starting_items, 
        self.operation,
        self.test_division,
        self.branch_true,
        self.branch_false)


def from_file(filename : str) -> List[Monkey]:
  monkeys : List[Monkey] = []
  current_monkey : Optional[MonkeyBuilder] = None
  with open(filename) as f:
    for line in f.readlines():
      line = line.strip()
      match line[0]:
        case 'M':
          if current_monkey:
            monkeys.append(current_monkey.build())
          l = line.split()
          current_monkey = MonkeyBuilder(l[-1][:-1])
        case 'S' if current_monkey:
          current_monkey.starting_items = []
          _, item_worry_levels = line.split(':')
          levels = [int(i.strip()) for i in item_worry_levels.split(',')]
          for index, level in enumerate(levels):
            current_monkey.starting_items.append(
              WorryItem(f'{current_monkey.id}~i{index}l{level}', level))
        case 'O' if current_monkey:
          _, operation_text = line.split(':')
          t1, op, t2 = operation_text.strip().split()
          # Just support "old op int" and "old op old".
          if t1 != 'old':
            raise Exception('Unsupported operation {t1}.')
          # old op old
          if t2 == 'old':
            match op:
              case '+':
                current_monkey.operation = lambda x : x + x
              case '*':
                current_monkey.operation = lambda x : x * x
          # old op int
          else:
            t2 = int(t2)
            match op:
              case '+':
                current_monkey.operation = lambda x : x + t2
              case '*':
                current_monkey.operation = lambda x : x * t2
        case 'T' if current_monkey:
          _, test_text = line.split(':')
          d, b, v = test_text.split()
          if f'{d} {b}' != 'divisible by':
            raise Exception(f'Unknown test: {test_text}')
          current_monkey.test_division = int(v)
        case 'I' if current_monkey:
          if_name, if_action = line.split(':')
          _, _, _, id = if_action.strip().split()
          _, b = if_name.split()
          match b:
            case 'true':
              current_monkey.branch_true = id
            case 'false':
              current_monkey.branch_false = id
            case _:
              raise Exception('Unable to handle condition {b}')
          



  return monkeys