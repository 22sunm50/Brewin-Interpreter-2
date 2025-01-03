# Brewin Interpreter Program
## Overview
This repository contains the implementation of a Brewin Interpreter. The Brewin language is a subset of programming languages inspired by C++, Python, and Lisp. This repository builds an interpreter capable of running simple Brewin programs.

The project is divided into two phases:

1. **Brewin Interpreter 1**: A basic interpreter for Brewin v1 with limited functionality.
2. **Brewin Interpreter 2**: An enhanced interpreter with additional features such as functions, boolean support, and control structures.

## Features
### Brewin Interpreter 1
- Supports:
  1. Variable definitions, assignments, and printing.
  2. Arithmetic operations: addition (+) and subtraction (-).
  3. `print()` and `inputi()` function calls.
- Abstract Syntax Tree (AST)
  1. Nodes for programs, functions, statements, variables, values, and expressions.
 
### Brewin Interpreter 2
- Extended Features:
  1. Functions with parameters, recursion, and return values.
  2. Additional data types: boolean and nil.
  3. Extended arithmetic operations: multiplication, division, and unary negation.
  4. Logical and comparison operators.
  5. Control structures: `if`, `if-else`, and `for` loops.
- Enhanced AST Nodes:
  1. Nodes for arguments, conditional blocks, and loops.
 
## Usage
### Prerequisites
- Python 3.11
- Ensure intbase.py, brewparse.py, and brewlex.py are in the project directory.

### Running the Interpreter
To run a Brewin program within `interpreterv1.py` or `interpreterv2.py`:
1. Create an instance of the Interpreter class.
2. Pass a Brewin program as a string to the run() method.
   For Example:
  ```
  def main():
    program = """
  func foo(a) {
    print("a: ", a);
    return a + 1;
  }
  
  func bar(b) {
    print(b);
  }
  
  func main() {
    var x;
    x = foo(5);
    bar(x);
  }
  
  /*
  *OUT*
  a: 5
  6
  *OUT*
  */
                  """
    interpreter = Interpreter()
    interpreter.run(program)
  
  
  if __name__ == "__main__":
      main()
  ```
## Files in the Repository
- interpreterv1.py: Interpreter for Brewin v1.
- interpreterv2.py: Interpreter for the enhanced Brewin language.
- element.py: Class definition for AST nodes.
- README.md: This file.

## Error Handling
### Brewin Interpreter 1
- Error handling is limited to the specified scenarios.
### Brewin Interpreter 2
- `nil` values may behave unpredictably in specific cases not outlined in the spec.
- Division by zero has undefined behavior.
