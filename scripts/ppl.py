import os
import sys
import re
from datetime import time


def cls_statement():
    os.system('cls' if os.name == 'nt' else 'clear')


def newline():
    print(os.linesep)


class PPLCommands:
    def __init__(self, code):
        self.code = code.split('\n')
        self.variables = {}
        self.current_line = 0
        self.for_loops = {}

    def __add__(self, other):
        return self + other

    def run(self):
        while self.current_line < len(self.code):
            self.parse_line(self.code[self.current_line])
            self.current_line += 1

    def parse_line(self, line):
        if line.startswith('PRINT'):
            self.print_statement(line)
        elif line.startswith('LET'):
            self.let_statement(line)
        elif line.startswith('IF'):
            self.if_statement(line)
        elif line.startswith('GOTO'):
            self.goto_statement(line)
        elif line.startswith('CLS'):
            cls_statement()
        elif line.startswith('FOR'):
            self.for_statement(line)

    def reserved_variables(self):
        reserved = ['while', 'print', 'let', 'if', 'else', 'elif', 'for', 'in', 'range', 'break', 'continue', 'return', 'def', 'class', 'from', 'import', 'as', 'try', 'except', 'finally', 'with', 'raise', 'assert', 'yield', 'lambda', 'pass', 'del', 'global', 'nonlocal', 'True', 'False', 'None', 'and', 'or', 'not', 'is', 'lambda', 'await', 'async']
        if self in reserved:
            return self + '_'

    def println(*args):
        print(*args + (os.linesep,))

    def newlines(self):
        for i in range(self):
            print(os.linesep)

    def sprintln(*args):
        print(*args)

    def mprintln(*args):
        print(*args)

    def forward(self):
        sys.stdout.write("\033[%dC" % self)

    def back(self):
        sys.stdout.write("\033[%dD" % self)

    def print_statement(self, line):
        value = re.findall(r'PRINT\s+(.+)', line)[0].strip()
        if value.startswith('"') and value.endswith('"'):
            print(value[1:-1])
        else:
            print(self.variables.get(value, 0))

    def let_statement(self, line):
        variable, value = re.findall(r'LET\s+(\w+)\s*=\s*(.+)', line)[0]
        self.variables[variable] = int(value)

    def goto_statement(self, line):
        goto_line = int(re.findall(r'GOTO\s+(\d+)', line)[0])
        self.current_line = goto_line - 1

    def if_statement(self, line):
        condition, goto_line = re.findall(r'IF\s+(.+)\s+GOTO\s+(\d+)', line)[0]
        var1, op, var2 = re.findall(r'(\w+)\s*([=<>])\s*(\w+)', condition)[0]

        var1_value = self.variables.get(var1, 0)
        var2_value = self.variables.get(var2, 0)

        if ((op == '=' and var1_value == var2_value) or
                (op == '<' and var1_value < var2_value) or
                (op == '>' and var1_value > var2_value)):
            self.current_line = int(goto_line) - 1

    def for_statement(self, line):
        counter_var, start, end, line_num = re.findall(r'FOR\s+(\w+)\s*=\s*(\d+)\s+TO\s+(\d+)\s+GOTO\s+(\d+)', line)[0]
        start, end, line_num = int(start), int(end), int(line_num)

        if counter_var not in self.for_loops:
            self.variables[counter_var] = start
            self.for_loops[counter_var] = {'start': start, 'end': end, 'goto': line_num}
        else:
            self.variables[counter_var] += 1
            if self.variables[counter_var] <= self.for_loops[counter_var]['end']:
                self.current_line = line_num - 1
            else:
                del self.for_loops[counter_var]

    def inkey_statement(self, line):
        variable = re.findall(r'INKEY\s+(\w+)', line)[0]
        self.variables[variable] = ord(input()[0])

    def input_(self):
        return input(self)

