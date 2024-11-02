# Add to spec:
# - printing out a nil value is undefined

from env_v1 import EnvironmentManager
from type_valuev1 import Type, Value, create_value, get_printable
from intbase import InterpreterBase, ErrorType
from brewparse import parse_program


# Main interpreter class
class Interpreter(InterpreterBase):
    # constants
    BIN_OPS = {'+', '-', '*', '/', '==', '<', '<=', '>', '>=', '!='}

    # methods
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.trace_output = trace_output
        self.__setup_ops()

    # run a program that's provided in a string
    # usese the provided Parser found in brewparse.py to parse the program
    # into an abstract syntax tree (ast)
    def run(self, program):
        ast = parse_program(program)
        self.__set_up_function_table(ast)
        main_func = self.__get_func_by_name("main")
        self.env = EnvironmentManager()
        self.__run_statements(main_func.get("statements"))

    # creates a mapping of function names to their AST nodes, 
        # good for: quick look-up of functions during execution.
    def __set_up_function_table(self, ast):
        self.func_name_to_ast = {}
        for func_def in ast.get("functions"):
            func_name = func_def.get("name")
            param_count = len(func_def.get("args"))
            self.func_name_to_ast[(func_name, param_count)] = func_def # for func overloading: use (name, param_count) tuple as the key

    def __get_func_by_name(self, name):
        if name not in self.func_name_to_ast:
            super().error(ErrorType.NAME_ERROR, f"Function {name} not found")
        return self.func_name_to_ast[name]

    def __run_statements(self, statements):
        # all statements of a function are held in arg3 of the function AST node
        print(f"🗣️ Entered run_statements! statements list = {statements}")
        for statement in statements:
            if self.trace_output:
                print(statement)
            if statement.elem_type == InterpreterBase.FCALL_NODE:
                self.__call_func(statement)
            elif statement.elem_type == "=":
                self.__assign(statement)
            elif statement.elem_type == InterpreterBase.VAR_DEF_NODE:
                self.__var_def(statement)
            elif statement.elem_type == "if":
                self.__handle_if(statement)
            elif statement.elem_type == "for":
                self.__handle_for(statement)

    def __call_func(self, call_node):
        func_name = call_node.get("name")
        if func_name == "print":
            return self.__call_print(call_node)
        if func_name == "inputi":
            return self.__call_input(call_node)

        # add code here later to call other functions
        super().error(ErrorType.NAME_ERROR, f"Function {func_name} not found")

    def __call_print(self, call_ast):
        print(f"🖨️ Entered the print function")
        output = ""
        for arg in call_ast.get("args"):
            print(f"🖨️ print arg: {arg}")
            result = self.__eval_expr(arg)  # result gives a Value object
            print(f"🖨️ result after __eval_expr: {result}")
            # BOOLS:
            if result.type() == Type.BOOL:
                output += "true" if result.value() else "false"
            else: 
                output = output + get_printable(result)
            print(f"🖨️ the output: {output}")
        super().output(output)
        return Value(Type.NIL, None)  # print returns 'nil' (needed within an expression)

    def __call_input(self, call_ast):
        args = call_ast.get("args")
        if args is not None and len(args) == 1:
            result = self.__eval_expr(args[0])
            super().output(get_printable(result))
        elif args is not None and len(args) > 1:
            super().error(
                ErrorType.NAME_ERROR, "No inputi() function that takes > 1 parameter"
            )
        inp = super().get_input()
        if call_ast.get("name") == "inputi":
            return Value(Type.INT, int(inp))
        if call_ast.get("name") == "inputs":
            return Value(Type.STRING, str(inp))

    def __assign(self, assign_ast):
        var_name = assign_ast.get("name")
        value_obj = self.__eval_expr(assign_ast.get("expression"))
        if not self.env.set(var_name, value_obj):
            super().error(
                ErrorType.NAME_ERROR, f"Undefined variable {var_name} in assignment"
            )

    def __var_def(self, var_ast):
        var_name = var_ast.get("name")
        if not self.env.create(var_name, Value(Type.INT, 0)):
            super().error(
                ErrorType.NAME_ERROR, f"Duplicate definition for variable {var_name}"
            )

    def __eval_expr(self, expr_ast):
        print(f"💾 Entered __eval_expr!")
        if expr_ast.elem_type == InterpreterBase.INT_NODE:
            return Value(Type.INT, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.STRING_NODE:
            return Value(Type.STRING, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.BOOL_NODE:
            return Value(Type.BOOL, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.NIL_NODE:
            return Value(Type.NIL, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.VAR_NODE:
            var_name = expr_ast.get("name")
            val = self.env.get(var_name)
            print(f"💾 got val from var: {val}")
            if val is None:
                super().error(ErrorType.NAME_ERROR, f"Variable {var_name} not found")
            return val
        if expr_ast.elem_type == InterpreterBase.FCALL_NODE:
            return self.__call_func(expr_ast)
        if expr_ast.elem_type in Interpreter.BIN_OPS or expr_ast.elem_type in {"&&", "||"}:
            return self.__eval_op(expr_ast)
        if expr_ast.elem_type == 'neg' or expr_ast.elem_type == '!':
            operand = self.__eval_expr(expr_ast.get("op1"))
            if expr_ast.elem_type == 'neg':
                if operand.type() != Type.INT:
                    super().error(ErrorType.TYPE_ERROR, "(- or 'neg') requires an INT operand")
                return Value(Type.INT, -operand.value())
            elif expr_ast.elem_type == '!':
                if operand.type() != Type.BOOL:
                    super().error(ErrorType.TYPE_ERROR, "(!) requires a BOOL operand")
                return Value(Type.BOOL, not operand.value())

    def __eval_op(self, arith_ast):
        print(f"🤖 Entered __eval_op")
        print(f"🤖 the ops are: {arith_ast.get('op1')} and {arith_ast.get('op2')}")
        # 🍅🍅🍅 this handles strict evaluation already i think
        left_value_obj = self.__eval_expr(arith_ast.get("op1")) # returns type Value
        left_type = left_value_obj.type()
        right_value_obj = self.__eval_expr(arith_ast.get("op2")) # returns type Value
        right_type = right_value_obj.type()
        operator = arith_ast.elem_type
        print(f"🤖 In __eval_op: left type = {left_type} | right type = {right_type}")

        # special: "==" and "!="
        if operator == "==" or operator == "!=":
            # check if diff types: always not equal
            if left_type != right_type:
                return Value(Type.BOOL, operator == "!=")  # True for "!=", False for "=="
            f = self.op_to_lambda[left_type][operator] # same type: get lambda for the operator and run it
            return f(left_value_obj, right_value_obj)
        if left_type != right_type:
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible types [{left_type} and {right_type}] for {arith_ast.elem_type} operation",
            )
        if arith_ast.elem_type not in self.op_to_lambda[left_type]:
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible operator {arith_ast.get_type} for type {left_type}",
            )
        f = self.op_to_lambda[left_type][arith_ast.elem_type]
        return f(left_value_obj, right_value_obj)

    def __setup_ops(self):
        # dict of ops to corresponding lambda
        self.op_to_lambda = {}
        # INT
        # arithmetic
        self.op_to_lambda[Type.INT] = {}
        self.op_to_lambda[Type.INT]["+"] = lambda x, y: Value(x.type(), x.value() + y.value())
        self.op_to_lambda[Type.INT]["-"] = lambda x, y: Value(x.type(), x.value() - y.value())
        self.op_to_lambda[Type.INT]["*"] = lambda x, y: Value(x.type(), x.value() * y.value())
        self.op_to_lambda[Type.INT]["/"] = lambda x, y: Value(x.type(), x.value() // y.value())  # integer division
        # comparison
        self.op_to_lambda[Type.INT]["=="] = lambda x, y: Value(Type.BOOL, x.value() == y.value())
        self.op_to_lambda[Type.INT]["!="] = lambda x, y: Value(Type.BOOL, x.value() != y.value())
        self.op_to_lambda[Type.INT][">"] = lambda x, y: Value(Type.BOOL, x.value() > y.value())
        self.op_to_lambda[Type.INT][">="] = lambda x, y: Value(Type.BOOL, x.value() >= y.value())
        self.op_to_lambda[Type.INT]["<"] = lambda x, y: Value(Type.BOOL, x.value() < y.value())
        self.op_to_lambda[Type.INT]["<="] = lambda x, y: Value(Type.BOOL, x.value() <= y.value())
        
        # BOOL
        self.op_to_lambda[Type.BOOL] = {}
        # logical
        self.op_to_lambda[Type.BOOL]["&&"] = lambda x, y: Value(Type.BOOL, x.value() and y.value())
        self.op_to_lambda[Type.BOOL]["||"] = lambda x, y: Value(Type.BOOL, x.value() or y.value())
        # comparison
        self.op_to_lambda[Type.BOOL]["=="] = lambda x, y: Value(Type.BOOL, x.value() == y.value())
        self.op_to_lambda[Type.BOOL]["!="] = lambda x, y: Value(Type.BOOL, x.value() != y.value())

        # STRING
        self.op_to_lambda[Type.STRING] = {}
        # concatenation
        self.op_to_lambda[Type.STRING]["+"] = lambda x, y: Value(Type.STRING, x.value() + y.value())
        # comparison
        self.op_to_lambda[Type.STRING]["=="] = lambda x, y: Value(Type.BOOL, x.value() == y.value())
        self.op_to_lambda[Type.STRING]["!="] = lambda x, y: Value(Type.BOOL, x.value() != y.value())

        # NIL
        self.op_to_lambda[Type.NIL] = {}
        self.op_to_lambda[Type.NIL]["=="] = lambda x, y: Value(Type.BOOL, x.type() == y.type())
        self.op_to_lambda[Type.NIL]["!="] = lambda x, y: Value(Type.BOOL, x.type() != y.type())

    def __handle_if(self, if_ast):
        # evaluate the condition
        condition_expr = if_ast.get("condition")
        condition_value = self.__eval_expr(condition_expr)
        
        # ensure the condition is a boolean
        if condition_value.type() != Type.BOOL:
            super().error(ErrorType.TYPE_ERROR, "Condition in if statement must evaluate to a boolean")

        if_statements = if_ast.get("statements")
        else_statements = if_ast.get("else_statements")

        # execute the appropriate block based on the condition
        if condition_value.value():  # true if
            self.__run_statements(if_statements)
        elif else_statements is not None:  # false & else block exists
            self.__run_statements(else_statements)

    def __handle_for(self, for_ast):
        init_expr = for_ast.get("init")             # initialization expression
        condition_expr = for_ast.get("condition")   # condition to evaluate
        update_expr = for_ast.get("update")         # update expression
        body_statements = for_ast.get("statements") # statements in the loop body

        self.__assign(init_expr)                    # assign the initialization once

        while True:
            # eval the condition expression
            condition_value = self.__eval_expr(condition_expr)

            # CHECK: the condition is a boolean
            if condition_value.type() != Type.BOOL:
                super().error(ErrorType.TYPE_ERROR, f"For loop condition ({condition_value}) isn't a boolean")

            # if condition is false: stop loop
            if not condition_value.value():
                break
            self.__run_statements(body_statements)

            # update expression
            self.__assign(update_expr)

def main():
  program = """func main() {
                    var i;
                    for (i = 0; i < 6; i = i + 1) {
                        print(i);
                        if (i == 3){
                            print("reached if within for loop");
                        }
                        else{
                            print("on an iteration thats not #3");
                        }
                    }
                    }
                    """
  interpreter = Interpreter()
  interpreter.run(program)


if __name__ == "__main__":
    main()