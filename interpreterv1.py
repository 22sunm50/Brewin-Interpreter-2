# Add to spec:
# - printing out a nil value is undefined

from env_v1 import EnvironmentManager
from type_valuev1 import Type, Value, create_value, get_printable
from intbase import InterpreterBase, ErrorType
from brewparse import parse_program


# Main interpreter class
class Interpreter(InterpreterBase):
    # constants
    BIN_OPS = {"+", "-"}

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
            self.func_name_to_ast[func_def.get("name")] = func_def

    def __get_func_by_name(self, name):
        if name not in self.func_name_to_ast:
            super().error(ErrorType.NAME_ERROR, f"Function {name} not found")
        return self.func_name_to_ast[name]

    def __run_statements(self, statements):
        # all statements of a function are held in arg3 of the function AST node
        for statement in statements:
            if self.trace_output:
                print(statement)
            if statement.elem_type == InterpreterBase.FCALL_NODE:
                self.__call_func(statement)
            elif statement.elem_type == "=":
                self.__assign(statement)
            elif statement.elem_type == InterpreterBase.VAR_DEF_NODE:
                self.__var_def(statement)

    def __call_func(self, call_node):
        func_name = call_node.get("name")
        if func_name == "print":
            return self.__call_print(call_node)
        if func_name == "inputi":
            return self.__call_input(call_node)

        # add code here later to call other functions
        super().error(ErrorType.NAME_ERROR, f"Function {func_name} not found")

    def __call_print(self, call_ast):
        output = ""
        for arg in call_ast.get("args"):
            result = self.__eval_expr(arg)  # result is a Value object
            output = output + get_printable(result)
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
            return Value(Type.STRING, int(inp))

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
        if expr_ast.elem_type == InterpreterBase.INT_NODE:
            return Value(Type.INT, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.STRING_NODE:
            return Value(Type.STRING, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.VAR_NODE:
            var_name = expr_ast.get("name")
            val = self.env.get(var_name)
            if val is None:
                super().error(ErrorType.NAME_ERROR, f"Variable {var_name} not found")
            return val
        if expr_ast.elem_type == InterpreterBase.FCALL_NODE:
            return self.__call_func(expr_ast)
        if expr_ast.elem_type in Interpreter.BIN_OPS:
            return self.__eval_op(expr_ast)

    def __eval_op(self, arith_ast):
        print(f"🤖 Entered __eval_op")
        left_value_obj = self.__eval_expr(arith_ast.get("op1")) # returns type Value
        left_type = left_value_obj.type()
        right_value_obj = self.__eval_expr(arith_ast.get("op2")) # returns type Value
        right_type = right_value_obj.type()
        operator = arith_ast.elem_type
        print(f"🤖 In __eval_op: left type = {left_type} | right type = {right_type}")

        # special: "==" and "!="
        if operator == "==" or operator == "!=":
            # check if diff types
            if left_type != right_type:
                # diff types: always not equal
                return Value(Type.BOOL, operator == "!=")  # True for "!=", False for "=="
            # same type: get lambda for the operator and run it
            f = self.op_to_lambda[left_type][operator]
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
        self.op_to_lambda[Type.BOOL]["!"] = lambda x: Value(Type.BOOL, not x.value())
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


def main():
  program = """func main() {
                    print("abc"+"def");    /* prints abcdef */
                    }
                    """
  interpreter = Interpreter()
  interpreter.run(program)


if __name__ == "__main__":
    main()