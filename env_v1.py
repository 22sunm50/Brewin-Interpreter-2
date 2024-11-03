# The EnvironmentManager class keeps a mapping between each variable (aka symbol)
# in a brewin program and the value of that variable - the value that's passed in can be
# anything you like. In our implementation we pass in a Value object which holds a type
# and a value (e.g., Int, 10).
class EnvironmentManager:
    def __init__(self):
        self.environment = [[{}]]

    # enter new func
    def push_func_stack(self):
        self.environment.append([{}])

    # exit a func
    def pop_func_stack(self):
        if len(self.environment) > 0:
            self.environment.pop()
        else:
            raise RuntimeError("Michelle!! check whats wrong bc u cannot pop anymore func stacks on the EnvironmentManager!")

    # enter an if/for block
    def push_dict(self):
        if not self.environment:
            raise RuntimeError("🙅‍♀️ Michelle!! check whats wrong bc no func stack available to push a new dictionary!")
        self.environment[-1].append({})

    # exit if/for block
    def pop_dict(self):
        if len(self.environment) > 0 and len(self.environment[-1]) > 1:
            self.environment[-1].pop()
        else:
            raise RuntimeError("🙅‍♀️ Michelle!! check whats wrong bc u cannot pop anymore dicts on the stack!")

    # gets the data from var name (going from inner -> outer dict)
    def get(self, symbol):
        if not self.environment:
            return None  # no scope available
        for env in reversed(self.environment[-1]):
            if symbol in env:
                return env[symbol]
        return None

    # set the data from var name (in innermost dict)
    # if name not found, move to outter dict
    def set(self, symbol, value):
        if not self.environment:
            return False  # 🍅 no scope available
        for env in reversed(self.environment[-1]):
            if symbol in env:
                env[symbol] = value
                return True
        return False # var not found in any scope :(


    # create new var in curr innermost dict
    def create(self, symbol, start_val):
        if not self.environment:
            raise RuntimeError("🙅‍♀️ Michelle!! check whats wrong bc no func stack available to create new var!")

        current_dict_stack = self.environment[-1][-1]
        if symbol not in current_dict_stack: 
            current_dict_stack[symbol] = start_val
            return True
        return False # var already exists in curr dict
