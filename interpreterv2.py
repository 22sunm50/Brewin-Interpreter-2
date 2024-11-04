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

    def run(self, program):
        ast = parse_program(program)
        self.__set_up_function_table(ast)
        main_func = self.__get_func_by_name("main", 0)
        self.env = EnvironmentManager()
        self.__run_statements(main_func.get("statements"))

    def __set_up_function_table(self, ast):
        self.func_name_to_ast = {}
        for func_def in ast.get("functions"):
            func_name = func_def.get("name")
            arg_count = len(func_def.get("args"))
            self.func_name_to_ast[(func_name, arg_count)] = func_def # for func overloading: use (name, param_count) tuple as the key

    def __get_func_by_name(self, name, arg_count):
        func_key = (name, arg_count)
        if func_key not in self.func_name_to_ast:
            super().error(ErrorType.NAME_ERROR, f"Function {name} w/ arg_count {arg_count} not found")
        return self.func_name_to_ast[func_key]

    def __run_statements(self, statements):
        # all statements of a function are held in arg3 of the function AST node
        result_tuple = (Value(Type.NIL, None), False)
        for statement in statements:
            # 🍅: to deal with returning out of the IF block and straight back out the func?
            if result_tuple[1] == True:
                return result_tuple
            if statement.elem_type == "return":
                result_tuple = self.__handle_return(statement)
                return result_tuple
            if statement.elem_type == InterpreterBase.FCALL_NODE:
                result_tuple = self.__call_func(statement)
                if result_tuple[1]: # ret_early = True
                    return result_tuple 
            elif statement.elem_type == "=":
                self.__assign(statement)
            elif statement.elem_type == InterpreterBase.VAR_DEF_NODE:
                self.__var_def(statement)
            elif statement.elem_type == "if":
                result_tuple = self.__handle_if(statement)
                if result_tuple[1]: # ret_early = True
                    return result_tuple
            elif statement.elem_type == "for":
                result_tuple = self.__handle_for(statement)
                if result_tuple[1]: # ret_early = True
                    return result_tuple 
        return Value(Type.NIL, None), False # no return statement, so return nil

    def __call_func(self, call_node):
        func_name = call_node.get("name")
        
        if func_name == "print":
            return self.__call_print(call_node), False
        if func_name == "inputi" or func_name == "inputs":
            return self.__call_input(call_node), False

        args = [self.__eval_expr(arg) for arg in call_node.get("args")]
        arg_count = len(args)
        func_def = self.__get_func_by_name(func_name, arg_count)
        return self.__run_func(func_def, args) # __run_func returns (result, ret_early)

    def __call_print(self, call_ast):
        output = ""
        count = 0
        for arg in call_ast.get("args"):
            result = self.__eval_expr(arg)  # result gives a Value object
            # BOOLS:
            if result.type() == Type.BOOL:
                output += "true" if result.value() else "false"
            # elif result.value() == True or result.value() == False: # turn primitive Python boolean into lowercase
            #     output += "true" if result.value() else "false"
            elif result.type() != Type.NIL:  # skip nil values in print
                output += get_printable(result)
            count += 1
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
            if val is None:
                super().error(ErrorType.NAME_ERROR, f"Variable {var_name} not found")
            return val
        if expr_ast.elem_type == InterpreterBase.FCALL_NODE:        
            # Handle the print function as a special case
            func_name = expr_ast.get("name")
            if func_name == "print":
                return self.__call_print(expr_ast)  # Call print only once
            # For other function calls
            result, _ = self.__call_func(expr_ast)
            return result
            
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
        # handles strict evaluation already?
        left_value_obj = self.__eval_expr(arith_ast.get("op1")) # returns type Value
        left_type = left_value_obj.type()
        right_value_obj = self.__eval_expr(arith_ast.get("op2")) # returns type Value
        right_type = right_value_obj.type()
        operator = arith_ast.elem_type

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
                f"Incompatible types [{left_type} and {right_type}] for {operator} operation",
            )
        if operator not in self.op_to_lambda[left_type]:
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible operator {operator} for type {left_type}",
            )
        f = self.op_to_lambda[left_type][operator]
        result_val_obj = (f(left_value_obj, right_value_obj))
        return result_val_obj

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
        
        # CHECK: the condition is a boolean
        if condition_value.type() != Type.BOOL:
          super().error(ErrorType.TYPE_ERROR, f"Condition in if statement must evaluate to a boolean. The condition is type: {condition_value.type()}")

        # push new dict for IF block
        self.env.push_dict()
        if condition_value.value():  # true condition
            # self.__run_statements(if_ast.get("statements"))
            result, ret_early = self.__run_statements(if_ast.get("statements"))
            if ret_early:
                self.env.pop_dict()  # pop out!
                return result, True
        elif if_ast.get("else_statements") is not None:  # false & else block exists
            # self.__run_statements(if_ast.get("else_statements"))
            result, ret_early = self.__run_statements(if_ast.get("else_statements"))
            if ret_early:
                self.env.pop_dict()  # ensure we clean up before returning
                return result, True

        # after running statements, exit IF block
        self.env.pop_dict()
        return Value(Type.NIL, None), False  # no early return happened

    def __handle_for(self, for_ast):
        init_expr = for_ast.get("init")
        condition_expr = for_ast.get("condition")
        update_expr = for_ast.get("update")
        body_statements = for_ast.get("statements")

        self.__assign(init_expr) # assign the initialization once

        while True:
            self.env.push_dict()
            # eval the condition expression
            condition_value = self.__eval_expr(condition_expr)

            # CHECK: the condition is a boolean
            if condition_value.type() != Type.BOOL:
                super().error(ErrorType.TYPE_ERROR, f"Loop condition ({condition_value}) isn't a boolean")

            # if condition is false: exit loop
            if not condition_value.value():
                self.env.pop_dict()
                break

            # run statements & check for ret_early
            result_tuple = self.__run_statements(body_statements)
            if result_tuple[1]:
                self.env.pop_dict()
                return result_tuple
            
            self.__assign(update_expr) # update
            self.env.pop_dict()
        return Value(Type.NIL, None), False

    def __handle_return(self, return_node):
        if return_node.get("expression") is not None:
            return self.__eval_expr(return_node.get("expression")), True
        return Value(Type.NIL, None), True # return nil, and early return
    
    def __run_func(self, func_def, args):
        self.env.push_func_stack()

        # add args to new func stack
        params = func_def.get("args")
        for param, arg_value in zip(params, args):
            param = param.get('name')
            arg_value = create_value(arg_value.value())
            self.env.create(param, arg_value) # pass-by-value: copy arg value (puts args in curr env)

        result, ret_early = self.__run_statements(func_def.get("statements"))
        self.env.pop_func_stack()
        return result, ret_early
    
def main():
  program = """
func bar(a) {
  print(a);
}

func main() {
  bar(false || true);
}
                """
  interpreter = Interpreter()
  interpreter.run(program)


if __name__ == "__main__":
    main()