# The EnvironmentManager class keeps a mapping between each variable (aka symbol)
# in a brewin program and the value of that variable - the value that's passed in can be
# anything you like. In our implementation we pass in a Value object which holds a type
# and a value (e.g., Int, 10).
class EnvironmentManager:
    def __init__(self):
        self.environment = [{}]

    # for entering an if/for block
    def push_dict(self):
        self.environment.append({})

    # exiting if/for block
    def pop_dict(self):
        if len(self.environment) > 1:
            self.environment.pop()
        else:
            raise RuntimeError("Michelle!! check whats wrong bc u cannot pop anymore dicts on the stack!")

    # gets the data from var name (going from inner -> outer dict)
    def get(self, symbol):
        for env in reversed(self.environment):
            if symbol in env:
                return env[symbol]
        return None

    # set the data from var name (in innermost dict)
    # if name not found, move to outter dict
    def set(self, symbol, value):
        for env in reversed(self.environment):
            if symbol in env:
                env[symbol] = value
                return True
        return False # var not found in any scope :(


    # create new var in curr innermost dict
    def create(self, symbol, start_val):
        current_env = self.environment[-1]
        if symbol not in current_env: 
          current_env[symbol] = start_val
          return True
        return False # var already exists in curr dict
