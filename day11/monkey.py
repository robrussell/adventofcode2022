
from dataclasses import dataclass
from dataclasses import field
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

MonkeyId = str
WorryItemId = str
WorryOperation = Callable

# Don't bother factoring until numbers are bigger than this
START_FACTORING = 1_000_000_000_000

# Let's get some primes. Silly but quick enough.
def make_some_primes(how_many: int = 100) -> List[int]:
  def qf(n : int) -> List[int]:
    # It would be faster to give up after finding a second factor.
    # It would also be faster to try the primes we've already found.
    return [i for i in range(1, int(n/2) + 1) if n % i == 0]
  def fp(m : int) -> List[int]:
    return [i for i in range(1, m) if len(qf(i))==1]
  return fp(how_many)

PRIMES : Optional[List[int]] = None

def product(f : List[int]) -> int:
  r = 1
  for i in f:
    r *= i
  return r

def factor(n : int, PRIMES=PRIMES):
  """ Returns a list of factors of `n`. Each factor from PRIMES will show up
  just once. This is useful for answering whether n is divisible by the value.
  """
  if not PRIMES:
    PRIMES = make_some_primes()
  factors : List[int] = []
  for p in PRIMES:
    quotient, remainder = divmod(n, p)
    if remainder == 0:
      factors.append(p)
      n = quotient
  factors.append(n)
  return factors

@dataclass
class WorryItem:
  id : WorryItemId
  worry_level : int
  factors : List[int] = field(init=False)
  factors_fresh : bool = field(init=False, default=False)

class Monkey:
  def __init__(self, id : MonkeyId, 
      starting_items : List[WorryItem],
      operation : WorryOperation,
      factored_operation : WorryOperation,
      test_division : int,
      branch_true : MonkeyId,
      branch_false : MonkeyId):
    self.id_ : MonkeyId = id
    self.items_ : List[WorryItem] = starting_items
    self.operation_ : WorryOperation = operation
    self.factored_operation_ : WorryOperation = factored_operation
    self.test_division_ : int = test_division
    self.branch_true_ : MonkeyId = branch_true
    self.branch_false_ : MonkeyId = branch_false
    self.inspection_count_ : int = 0
    if (self.id_ == self.branch_true_
        or self.id_ == self.branch_false_):
      raise Exception(f'Monkey {self.id_} would throw to itself.')

  def catch(self, item : WorryItem):
    self.items_.append(item)
  
  def get_inspection_count(self):
    return self.inspection_count_

  def take_turn(self, throw : Callable, post_inpect_worry_reduction=True):
    """ The turn has 3 stages for each item:
      * Inspect the item. Apply the operation to the item's worry level.
      * Get bored with the item. Divide item's worry level by 3 (only in part 1).
      * Test the item's worry level and throw it accordingly.
      The throw function is called with a `MonkeyId` and a `WorryItem`.
    """
    for i in self.items_:
      self.inspection_count_ += 1
      if i.worry_level < START_FACTORING:
        i.worry_level = self.operation_(i.worry_level)
        if post_inpect_worry_reduction:
          i.worry_level //= 3
        target = (self.branch_true_
          if (i.worry_level % self.test_division_ == 0) 
          else self.branch_false_)
        print(f'{i.id} level {i.worry_level}, throw to {target}')
      else:
        if not i.factors_fresh:
          i.factors = factor(i.worry_level)
          i.factors_fresh = True
        i.factors = self.factored_operation_(i.factors)
        target = (self.branch_true_
          if (self.test_division_ in i.factors) 
          else self.branch_false_)
      throw(target, i)
    # All items have been thrown.
    self.items_.clear()

@dataclass
class MonkeyBuilder:
    # Identifier from input file
    id : MonkeyId
    # List of worry items from input file
    starting_items : Optional[List[WorryItem]] = field(init=False)
    # Math operation interpretted as a function
    operation : Optional[WorryOperation] = field(init=False)
    factored_operation : Optional[Callable] = field(init=False)
    # Number to use in division test
    test_division : Optional[int] = field(init=False)
    # ID of monkey to throw item to on True result
    branch_true : Optional[MonkeyId] = field(init=False)
    # ID of monkey to throw item to on False result
    branch_false : Optional[MonkeyId] = field(init=False)

    def build(self) -> Monkey:
      if not (self.operation and 
        self.factored_operation and 
        self.starting_items and 
        self.test_division and 
        self.branch_true and
        self.branch_false):
        raise Exception('Incomplete monkey.')
      return Monkey(self.id, 
        self.starting_items, 
        self.operation,
        self.factored_operation,
        self.test_division,
        self.branch_true,
        self.branch_false)


def from_file(filename : str) -> Dict[MonkeyId, Monkey]:
  monkeys : Dict[MonkeyId, Monkey] = dict()
  current_monkey : Optional[MonkeyBuilder] = None

  def make_op(op, t2):
    # old op old
    if t2 == 'old':
      match op:
        case '+':
          return lambda x : x + x
        case '*':
          return lambda x : x * x
    # old op int
    else:
      t2 = int(t2)
      match op:
        case '+':
          return lambda x : x + t2
        case '*':
          return lambda x : x * t2

  def make_factored_op(op, t2):
    # old op old
    if t2 == 'old':
      match op:
        case '+':
          def f(x):
            x.append(2)
            return x
          return f
        case '*':
          def f(x):
            x.extend(x)
            return x
          return f
    # old op int
    else:
      t2 = int(t2)
      match op:
        case '+':
          return lambda x : factor(product(x) + t2)
        case '*':
          def f(x):
            x.append(t2)
            return x
          return f

  with open(filename) as f:
    for line in f.readlines():
      line = line.strip()
      if not line:
        continue
      match line[0]:
        case 'M':
          if current_monkey:
            monkeys[current_monkey.id] = (current_monkey.build())
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
          _, operation_eq = line.split(':')
          _, operation_text = operation_eq.split('=')
          t1, op, t2 = operation_text.strip().split()
          # Just support "old op int" and "old op old".
          if t1 != 'old':
            raise Exception('Unsupported operation {t1}.')
          current_monkey.operation = make_op(op, t2)
          current_monkey.factored_operation = make_factored_op(op, t2)
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

  if current_monkey:
    monkeys[current_monkey.id] = (current_monkey.build())
  return monkeys