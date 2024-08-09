# MathScript - A Math programming language, by foxypiratecove37350

##########################################################
# INFORMATIONS
##########################################################

product_name = 'MathScript'
product_description = 'A Math programming language, by foxypiratecove37350'
debug_modes_list = ['lexer', 'parser', 'lexer-parser', 'all']
debug_modes_list_str = ', '.join(f"'{mode}'" for mode in debug_modes_list[:-1]) + f" or '{debug_modes_list[-1]}'" if len(debug_modes_list) != 1 else debug_modes_list[0]
version = {'major': 1, 'minor': 0, 'build': 1, 'revision': None}
version_str = f'{version['major']}{f'.{version['minor']}{f'.{version['build']}{f'.{version['revision']}' if version['revision'] is not None else ''}' if version['build'] is not None else ''}' if version['minor'] is not None else ''}'
debug_mode = False

##########################################################
# IMPORTS
##########################################################

import re
from strings_with_arrows import *
from mpmath import mpf, mpc, mp # type: ignore
from colorama import just_fix_windows_console # type: ignore
import string
import sys

just_fix_windows_console()
mp.dps = 1000

##########################################################
# CONSTANTS
##########################################################

DIGITS = '0123456789'
LETTERS = string.ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS

##########################################################
# ERRORS
##########################################################

class Error:
	def __init__(self, pos_start, pos_end, error_name, details):
		self.pos_start = pos_start
		self.pos_end = pos_end
		self.error_name = error_name

		formatted_text = ""
		current_line = ""
		char_count = 0

		for word in details.split():
			if char_count + len(word) > 60:
				formatted_text += current_line + "\n"
				current_line = word
				char_count = len(word)
			else:
				if current_line:
					current_line += " "
					char_count += 1
				current_line += word
				char_count += len(word)

		if current_line:
			formatted_text += current_line

		self.details = formatted_text
	
	def as_string(self):
		result  = f'{self.error_name}: {self.details}\n'
		result += f'File {self.pos_start.fn}, line {self.pos_start.ln + 1} at column {self.pos_start.col}'
		result += f'\n\n{string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)}'

		return result

class IllegalCharError(Error):
	def __init__(self, pos_start, pos_end, details):
		super().__init__(pos_start, pos_end, 'Illegal Character', details)

class ExpectedCharError(Error):
	def __init__(self, pos_start, pos_end, details):
		super().__init__(pos_start, pos_end, 'Expected Character', details)

class InvalidSyntaxError(Error):
	def __init__(self, pos_start, pos_end, details=''):
		super().__init__(pos_start, pos_end, 'Invalid Syntax', details)

class RTError(Error):
	def __init__(self, pos_start, pos_end, details, context):
		super().__init__(pos_start, pos_end, 'Runtime Error', details)
		self.context = context

	def as_string(self):
		result  = self.generate_traceback()
		result += f'{self.error_name}: {self.details}'
		result += f'\n\n{string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)}'

		return result
	
	def generate_traceback(self):
		result = ''
		pos = self.pos_start
		ctx = self.context

		while ctx:
			result = f'  File {pos.fn}, line {str(pos.ln + 1)}, in {ctx.display_name}\n' + result
			pos = ctx.parent_entry_pos
			ctx = ctx.parent

		return 'Traceback (most recent call last):\n' + result

##########################################################
# POSITION
##########################################################

class Position:
	def __init__(self, idx, ln, col, fn, ftxt):
		self.idx = idx
		self.ln = ln
		self.col = col
		self.fn = fn
		self.ftxt = ftxt

	def advance(self, current_char=None):
		self.idx += 1
		self.col += 1

		if current_char == '\n':
			self.ln += 1
			self.col = 0

		return self

	def copy(self):
		return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)

##########################################################
# TOKENS
##########################################################

TT_INTEGER      = 'INTEGER'
TT_DECIMAL      = 'DECIMAL'
TT_COMPLEX      = 'COMPLEX'
TT_STRING       = 'STRING'
TT_RSTRING      = 'RSTRING'
TT_IDENTIFIER   = 'IDENTIFIER'
TT_KEYWORD      = 'KEYWORD'
TT_PLUS         = 'PLUS'
TT_MINUS        = 'MINUS'
TT_MUL          = 'MUL'
TT_DIV          = 'DIV'
TT_POW          = 'POW'
TT_SUBSCRIPT    = 'SUBSCRIPT'
TT_EQ           = 'EQ'
TT_LPAREN       = 'LPAREN'
TT_RPAREN       = 'RPAREN'
TT_LSQUARE      = 'LSQUARE'
TT_RSQUARE      = 'RSQUARE'
TT_EE           = 'EE'
TT_NE           = 'NE'
TT_LT           = 'LT'
TT_GT           = 'GT'
TT_LTE          = 'LTE'
TT_GTE          = 'GTE'
TT_COMMA        = 'COMMA'
TT_ARROW        = 'ARROW'
TT_NEWLINE      = 'NEWLINE'
TT_EOF          = 'EOF'

KEYWORDS = [
	'and',
	'or',
	'not',
	'if',
	'elif',
	'else',
	'for',
	'to',
	'step',
	'while',
	'func',
	'then',
	'pass',
	'end',
	'return',
	'break',
	'continue'
]

class Token:
	def __init__(self, type_, value=None, pos_start=None, pos_end=None):
		self.type = type_
		self.value = value

		if pos_start:
			self.pos_start = pos_start.copy()
			self.pos_end = pos_start.copy()
			self.pos_end.advance()

		if pos_end:
			self.pos_end = pos_end.copy()

	def matches(self, type_, value):
		return self.type == type_ and self.value == value

	def __repr__(self):
		if isinstance(self.value, complex): return repr(self.value).replace('j', 'i')
		if self.value is not None: return f'{self.type}:{self.value}'
		return f'{self.type}'

##########################################################
# LEXER
##########################################################

class Lexer:
	def __init__(self, fn, text):
		self.fn = fn
		self.text = text
		self.pos = Position(-1, 0, -1, fn, text)
		self.current_char = None
		self.advance()

	def advance(self):
		self.pos.advance(self.current_char)
		self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

	def make_tokens(self):
		tokens = []

		while self.current_char is not None:
			if self.current_char in ' \t':
				self.advance()
			elif self.current_char == '#':
				self.skip_comment()
			elif self.current_char in ';\n':
				tokens.append(Token(TT_NEWLINE, pos_start=self.pos))
				self.advance()
			elif self.current_char in DIGITS:
				tokens.append(self.make_number())
			elif self.current_char in LETTERS:
				tokens.append(self.make_identifier())
			elif self.current_char in ('"', "'", '`'):
				token, error = self.make_string(self.current_char)
				if error: return [], error
				tokens.append(token)
			elif self.current_char == '+':
				tokens.append(Token(TT_PLUS, pos_start=self.pos))
				self.advance()
			elif self.current_char == '-':
				tokens.append(Token(TT_MINUS, pos_start=self.pos))
				self.advance()
			elif self.current_char == '*':
				tokens.append(Token(TT_MUL, pos_start=self.pos))
				self.advance()
			elif self.current_char == '/':
				tokens.append(Token(TT_DIV, pos_start=self.pos))
				self.advance()
			elif self.current_char == '^':
				tokens.append(Token(TT_POW, pos_start=self.pos))
				self.advance()
			elif self.current_char == '_':
				tokens.append(Token(TT_SUBSCRIPT, pos_start=self.pos))
				self.advance()
			elif self.current_char == '(':
				tokens.append(Token(TT_LPAREN, pos_start=self.pos))
				self.advance()
			elif self.current_char == ')':
				tokens.append(Token(TT_RPAREN, pos_start=self.pos))
				self.advance()
			elif self.current_char == '[':
				tokens.append(Token(TT_LSQUARE, pos_start=self.pos))
				self.advance()
			elif self.current_char == ']':
				tokens.append(Token(TT_RSQUARE, pos_start=self.pos))
				self.advance()
			elif self.current_char == '!':
				token, error = self.make_not_equals()
				if error: return [], error
				tokens.append(token)
			elif self.current_char == '=':
				tokens.append(self.make_equals())
			elif self.current_char == '<':
				tokens.append(self.make_less_than())
			elif self.current_char == '>':
				tokens.append(self.make_greater_than())
			elif self.current_char == ',':
				tokens.append(Token(TT_COMMA, pos_start=self.pos))
				self.advance()
			else:
				pos_start = self.pos.copy()
				char = self.current_char
				self.advance()
				return [], IllegalCharError(pos_start, self.pos, f'"{char}"')

		tokens.append(Token(TT_EOF, pos_start=self.pos))
		return tokens, None

	def make_number(self):
		num_str = ''
		dot_count = 0
		i_count = 0
		pos_start = self.pos.copy()

		while self.current_char is not None and self.current_char in DIGITS + '.i':
			if self.current_char == '.':
				if dot_count == 1: break
				dot_count += 1
			if self.current_char == 'i':
				if i_count == 1: break
				i_count += 1
			num_str += self.current_char.replace('i', 'j')

			self.advance()
		
		if i_count == 1:
			return Token(TT_COMPLEX, complex(num_str), pos_start, self.pos)

		if dot_count == 0:
			return Token(TT_INTEGER, int(num_str), pos_start, self.pos)
		else: return Token(TT_DECIMAL, float(num_str), pos_start, self.pos)

	def make_string(self, quote):
		string = ''
		tok_type = TT_RSTRING if quote == '`' else TT_STRING
		pos_start = self.pos.copy()
		escape_character = False
		self.advance()

		escape_characters = {
			'n': '\n',
			't': '\t',
			'\\': '\\'
		}

		prev_pos = self.pos.copy()

		while self.current_char is not None and (self.current_char != quote or escape_character):
			if tok_type == TT_STRING:
				if escape_character:
					if self.current_char in escape_characters:
						string += escape_characters.get(self.current_char)
					else:
						prev_char = self.current_char
						self.advance()
						return None, IllegalCharError(
							prev_pos, self.pos,
							f"Invalid escape sequence '\\{prev_char}'"
						)
					escape_character = False
				else:
					if self.current_char == '\\':
						escape_character = True
					else:
						string += self.current_char
			else:
				string += self.current_char

			prev_pos = self.pos.copy()
			self.advance()
		
		self.advance()
		return Token(tok_type, string, pos_start, self.pos), None

	def make_identifier(self):
		id_str = ''
		pos_start = self.pos.copy()

		while self.current_char is not None and self.current_char in LETTERS_DIGITS + '_':
			id_str += self.current_char
			self.advance()
		
		tok_type = TT_KEYWORD if id_str in KEYWORDS else TT_IDENTIFIER
		return Token(tok_type, id_str, pos_start, self.pos)

	def make_not_equals(self):
		pos_start = self.pos.copy()
		self.advance()

		if self.current_char == '=':
			self.advance()
			return Token(TT_NE, pos_start=pos_start, pos_end=self.pos), None

		self.advance()		
		return None, ExpectedCharError(pos_start, self.pos, "'=' (after '!')")

	def make_equals(self):
		tok_type = TT_EQ
		pos_start = self.pos.copy()
		self.advance()

		if self.current_char == '=':
			self.advance()
			tok_type = TT_EE
		elif self.current_char == '>':
			self.advance()
			tok_type = TT_ARROW

		return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

	def make_less_than(self):
		tok_type = TT_LT
		pos_start = self.pos.copy()
		self.advance()

		if self.current_char == '=':
			self.advance()
			tok_type = TT_LTE

		return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

	def make_greater_than(self):
		tok_type = TT_GT
		pos_start = self.pos.copy()
		self.advance()

		if self.current_char == '=':
			self.advance()
			tok_type = TT_GTE

		return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

	def skip_comment(self):
		self.advance()

		while self.current_char != '\n':
			self.advance()

		self.advance()

##########################################################
# NODES
##########################################################

class IntegerNode:
	def __init__(self, tok):
		self.tok = tok

		self.pos_start = self.tok.pos_start
		self.pos_end = self.tok.pos_end

	def __repr__(self):
		return f'{self.tok}'
	
class DecimalNode:
	def __init__(self, tok):
		self.tok = tok

		self.pos_start = self.tok.pos_start
		self.pos_end = self.tok.pos_end

	def __repr__(self):
		return f'{self.tok}'

class ComplexNode:
	def __init__(self, tok):
		self.tok = tok

		self.pos_start = self.tok.pos_start
		self.pos_end = self.tok.pos_end

	def __repr__(self):
		return f'{self.tok}'

class StringNode:
	def __init__(self, tok):
		self.tok = tok

		self.pos_start = self.tok.pos_start
		self.pos_end = self.tok.pos_end

	def __repr__(self):
		return f'{self.tok.type}:{repr(self.tok.value)}'

class ListNode:
	def __init__(self, element_nodes, pos_start, pos_end):
		self.element_nodes = element_nodes
		self.pos_start = pos_start
		self.pos_end = pos_end

	def __repr__(self):
		if len(self.element_nodes) == 0:
			return 'LIST:()'
		return f"LIST:({self.element_nodes[0]},{','.join(' ' + str(x) for x in self.element_nodes[1:])})"
	
class PassNode:
	def __init__(self, pos_start, pos_end):
		self.pos_start = pos_start
		self.pos_end = pos_end

	def __repr__(self):
			return 'PASS'

class VarAccessNode:
	def __init__(self, var_name_tok):
		self.var_name_tok = var_name_tok

		self.pos_start = self.var_name_tok.pos_start
		self.pos_end = self.var_name_tok.pos_end
	
	def __repr__(self):
		return f"VAR_ACCESS:{self.var_name_tok.value}"

class VarAssignNode:
	def __init__(self, var_name_tok, value_node):
		self.var_name_tok = var_name_tok
		self.value_node = value_node

		self.pos_start = self.var_name_tok.pos_start
		self.pos_end = self.value_node.pos_end
	
	def __repr__(self):
		return f"VAR_ASSIGN:({self.var_name_tok} = {self.value_node})"

class BinOpNode:
	def __init__(self, left_node, op_tok, right_node):
		self.left_node = left_node
		self.op_tok = op_tok
		self.right_node = right_node

		self.pos_start = self.left_node.pos_start
		self.pos_end = self.right_node.pos_end

	def __repr__(self):
		return f'({self.left_node}, {self.op_tok}, {self.right_node})'

class UnaryOpNode:
	def __init__(self, op_tok, node):
		self.op_tok = op_tok
		self.node = node
		
		self.pos_start = self.op_tok.pos_start
		self.pos_end = node.pos_end

	def __repr__(self):
		return f'({self.op_tok}, {self.node})'

class IfNode:
	def __init__(self, cases, else_case):
		self.cases = cases
		self.else_case = else_case

		self.pos_start = self.cases[0][0].pos_start
		self.pos_end = (self.else_case or self.cases[-1])[0].pos_end
	
	def __repr__(self):
		return f"IF:({', '.join(repr(x) for x in self.cases)}{', ' + self.else_case if self.else_case else ''})"

class ForNode:
	def __init__(self, var_name_tok, start_value_node, end_value_node, step_value_node, body_node, should_return_null):
		self.var_name_tok = var_name_tok
		self.start_value_node = start_value_node
		self.end_value_node = end_value_node
		self.step_value_node = step_value_node
		self.body_node = body_node
		self.should_return_null = should_return_null

		self.pos_start = self.var_name_tok.pos_start
		self.pos_end = self.body_node.pos_end

	def __repr__(self):
		return f"FOR:({self.var_name_tok.value}: {self.start_value_node} -> {self.end_value_node} {f'({self.step_value_node})' if self.step_value_node else '\b'} => {self.body_node})"

class WhileNode:
	def __init__(self, condition_node, body_node, should_return_null):
		self.condition_node = condition_node
		self.body_node = body_node
		self.should_return_null = should_return_null

		self.pos_start = self.condition_node.pos_start
		self.pos_end = self.body_node.pos_end

	def __repr__(self):
		return f"WHILE:({self.condition_node}? {self.body_node})"

class FuncDefNode:
	def __init__(self, var_name_tok, arg_name_toks, body_node, should_auto_return):
		self.var_name_tok = var_name_tok
		self.arg_name_toks = arg_name_toks
		self.body_node = body_node
		self.should_auto_return = should_auto_return

		if self.var_name_tok is not None:
			self.pos_start = self.var_name_tok.pos_start
		elif len(self.arg_name_toks) > 0:
			self.pos_start = self.arg_name_toks[0].pos_start
		else:
			self.pos_start = self.body_node.pos_start

		self.pos_end = self.body_node.pos_end
	
	def __repr__(self):
		return f"FUNC_DEF:({self.var_name_tok.value}({', '.join(repr(x) for x in self.arg_name_toks)}) => {self.body_node})"

class CallNode:
	def __init__(self, node_to_call, arg_nodes):
		self.node_to_call = node_to_call
		self.arg_nodes = arg_nodes

		self.pos_start = self.node_to_call.pos_start

		self.pos_end = self.arg_nodes[-1].pos_end if len(self.arg_nodes) > 0 else self.node_to_call.pos_end
	
	def __repr__(self):
		return f"FUNC_CALL:{self.node_to_call.var_name_tok.value}({', '.join(repr(x) for x in self.arg_nodes)})"

class ReturnNode:
	def __init__(self, node_to_return, pos_start, pos_end):
		self.node_to_return = node_to_return

		self.pos_start = pos_start
		self.pos_end = pos_end

	def __repr__(self):
		return f"RETURN:({self.node_to_return})"

class ContinueNode:
	def __init__(self, pos_start, pos_end):
		self.pos_start = pos_start
		self.pos_end = pos_end

	def __repr__(self):
		return f"CONTINUE"

class BreakNode:
	def __init__(self, pos_start, pos_end):
		self.pos_start = pos_start
		self.pos_end = pos_end

	def __repr__(self):
		return f"BREAK"

##########################################################
# PARSE RESULT
##########################################################

class ParseResult:
	def __init__(self):
		self.error = None
		self.node = None
		self.last_registered_advance_count = 0
		self.advance_count = 0
		self.to_reverse_count = 0

	def register_advancement(self, count=1):
		self.last_registered_advance_count = count
		self.advance_count += count

	def register(self, res):
		self.last_registered_advance_count = res.advance_count
		self.advance_count += res.advance_count
		if res.error: self.error = res.error
		return res.node
	
	def try_register(self, res):
		if res.error:
			self.to_reverse_count = res.advance_count
			return None
		return self.register(res)

	def success(self, node):
		self.node = node
		return self

	def failure(self, error):
		if self.error is None or self.last_registered_advance_count == 0:
			self.error = error
		return self

##########################################################
# PARSER
##########################################################

class Parser:
	def __init__(self, tokens):
		self.tokens = tokens
		self.tok_idx = -1
		self.advance()

	def advance(self, count=1):
		self.tok_idx += count
		if self.tok_idx < len(self.tokens):
			self.current_tok = self.tokens[self.tok_idx]
		
		return self.current_tok

	def parse(self):
		res = self.statements()
		if not res.error and self.current_tok.type != TT_EOF:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				"Expected '+', '-', '*', '/', '^', '==', '!=', '<', '>', <=', '>=', 'and' or 'or'"
			))
		return res

	######################################################

	def statements(self):
		res = ParseResult()
		statements = []
		pos_start = self.current_tok.pos_start.copy()

		while self.current_tok.type == TT_NEWLINE:
			res.register_advancement()
			self.advance()
		
		statement = res.register(self.statement())
		if res.error: return res
		statements.append(statement)

		more_statements = True

		while True:
			newline_count = 0
			while self.current_tok.type == TT_NEWLINE:
				res.register_advancement()
				self.advance()
				newline_count += 1
			if newline_count == 0:
				more_statements = False

			if not more_statements: break
			statement = res.try_register(self.statement())
			if not statement:
				self.advance(-res.to_reverse_count)
				more_statements = False
				continue

			statements.append(statement)

		return res.success(ListNode(
			statements,
			pos_start,
			self.current_tok.pos_end.copy()
		))

	def statement(self):
		res = ParseResult()
		pos_start = self.current_tok.pos_start.copy()

		if self.current_tok.matches(TT_KEYWORD, 'return'):
			res.register_advancement()
			self.advance()

			expr = res.try_register(self.expr())
			if not expr: self.advance(-res.to_reverse_count)

			return res.success(ReturnNode(expr, pos_start, self.current_tok.pos_start.copy()))
		
		if self.current_tok.matches(TT_KEYWORD, 'continue'):
			res.register_advancement()
			self.advance()
			return res.success(ContinueNode(pos_start, self.current_tok.pos_start.copy()))
		
		if self.current_tok.matches(TT_KEYWORD, 'break'):
			res.register_advancement()
			self.advance()
			return res.success(BreakNode(pos_start, self.current_tok.pos_start.copy()))

		expr = res.register(self.expr())
		if res.error: return res

		return res.success(expr)

	def if_expr(self):
		res = ParseResult()
		all_cases = res.register(self.if_expr_cases('if'))
		if res.error: return res
		cases, else_case = all_cases
		return res.success(IfNode(cases, else_case))
	
	def elif_expr(self):
		return self.if_expr_cases('elif')

	def else_expr(self):
		res = ParseResult()
		else_case = None

		if self.current_tok.matches(TT_KEYWORD, 'else'):
			res.register_advancement()
			self.advance()

			if self.current_tok.type == TT_NEWLINE:
				res.register_advancement()
				self.advance()

				statements = res.register(self.statements())
				if res.error: return res
				else_case = (statements, True)

				if self.current_tok.matches(TT_KEYWORD, 'end'):
					res.register_advancement()
					self.advance()
				else:
					return res.failure(InvalidSyntaxError(
						self.current_tok.pos_start, self.current_tok.pos_end,
						"Expected 'end'"
					))
			else:
				expr = res.register(self.statement())
				if res.error: return res
				else_case = (expr, False)

		return res.success(else_case)

	def elif_or_else_expr(self):
		res = ParseResult()
		cases, else_case = [], None

		if self.current_tok.matches(TT_KEYWORD, 'elif'):
			all_cases = res.register(self.elif_expr())
			if res.error: return res
			cases, else_case = all_cases
		else:
			else_case = res.register(self.else_expr())
			if res.error: return res

		return res.success((cases, else_case))
	
	def if_expr_cases(self, case_keyword):
		res = ParseResult()
		cases = []
		else_case = None

		if not self.current_tok.matches(TT_KEYWORD, case_keyword):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected '{case_keyword}'"
			))

		res.register_advancement()
		self.advance()

		condition = res.register(self.expr())
		if res.error: return res

		if not self.current_tok.matches(TT_KEYWORD, 'then'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected 'then'"
			))

		res.register_advancement()
		self.advance()

		if self.current_tok.type == TT_NEWLINE:
			res.register_advancement()
			self.advance()

			statements = res.register(self.statements())
			if res.error: return res
			cases.append((condition, statements, True))

			if self.current_tok.matches(TT_KEYWORD, 'end'):
				res.register_advancement()
				self.advance()
			else:
				all_cases = res.register(self.elif_or_else_expr())
				if res.error: return res
				new_cases, else_case = all_cases
				cases.extend(new_cases)
		else:
			expr = res.register(self.statement())
			if res.error: return res
			cases.append((condition, expr, False))

			all_cases = res.register(self.elif_or_else_expr())
			if res.error: return res
			new_cases, else_case = all_cases
			cases.extend(new_cases)

		return res.success((cases, else_case))

	def for_expr(self):
		res = ParseResult()

		if not self.current_tok.matches(TT_KEYWORD, 'for'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected 'for'"
			))

		res.register_advancement()
		self.advance()

		if self.current_tok.type != TT_IDENTIFIER:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected identifier"
			))

		var_name = self.current_tok
		res.register_advancement()
		self.advance()

		if self.current_tok.type != TT_EQ:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected '='"
			))
		
		res.register_advancement()
		self.advance()

		start_value = res.register(self.expr())
		if res.error: return res

		if not self.current_tok.matches(TT_KEYWORD, 'to'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected 'to'"
			))
		
		res.register_advancement()
		self.advance()

		end_value = res.register(self.expr())
		if res.error: return res

		if self.current_tok.matches(TT_KEYWORD, 'step'):
			res.register_advancement()
			self.advance()

			step_value = res.register(self.expr())
			if res.error: return res
		else:
			step_value = None

		if not self.current_tok.matches(TT_KEYWORD, 'then'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected 'then'"
			))

		res.register_advancement()
		self.advance()

		if self.current_tok.type == TT_NEWLINE:
			res.register_advancement()
			self.advance()

			body = res.register(self.statements())
			if res.error: return res

			if not self.current_tok.matches(TT_KEYWORD, 'end'):
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					f"Expected 'end'"
				))

			res.register_advancement()
			self.advance()

			return res.success(ForNode(var_name, start_value, end_value, step_value, body, True))

		body = res.register(self.statement())
		if res.error: return res

		return res.success(ForNode(var_name, start_value, end_value, step_value, body, False))

	def while_expr(self):
		res = ParseResult()

		if not self.current_tok.matches(TT_KEYWORD, 'while'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected 'while'"
			))

		res.register_advancement()
		self.advance()

		condition = res.register(self.expr())
		if res.error: return res

		if not self.current_tok.matches(TT_KEYWORD, 'then'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected 'then'"
			))

		res.register_advancement()
		self.advance()

		if self.current_tok.type == TT_NEWLINE:
			res.register_advancement()
			self.advance()

			body = res.register(self.statements())
			if res.error: return res

			if not self.current_tok.matches(TT_KEYWORD, 'end'):
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					f"Expected 'end'"
				))

			res.register_advancement()
			self.advance()

			return res.success(WhileNode(condition, body, True))

		body = res.register(self.statement())
		if res.error: return res

		return res.success(WhileNode(condition, body, False))

	def atom(self):
		res = ParseResult()
		tok = self.current_tok

		if tok.type == TT_INTEGER:
			res.register_advancement()
			self.advance()
			return res.success(IntegerNode(tok))
		if tok.type == TT_DECIMAL:
			res.register_advancement()
			self.advance()
			return res.success(DecimalNode(tok))
		if tok.type == TT_COMPLEX:
			res.register_advancement()
			self.advance()
			return res.success(ComplexNode(tok))
		if tok.type in (TT_STRING, TT_RSTRING):
			res.register_advancement()
			self.advance()
			if self.current_tok.type == TT_SUBSCRIPT:
				return res.success(res.register(self.bin_op(self.atom, (TT_SUBSCRIPT, ), self.expr, StringNode(tok))))
			return res.success(StringNode(tok))
		elif tok.type == TT_IDENTIFIER:
			res.register_advancement()
			self.advance()
			return res.success(VarAccessNode(tok))
		elif tok.type == TT_LPAREN:
			list_expr = res.register(self.list_expr())
			if res.error: return res
			
			if self.current_tok.type == TT_SUBSCRIPT:
				return res.success(res.register(self.bin_op(self.list_expr, (TT_SUBSCRIPT, ), self.expr, list_expr)))
			return res.success(list_expr)
		elif tok.matches(TT_KEYWORD, 'if'):
			if_expr = res.register(self.if_expr())
			if res.error: return res
			return res.success(if_expr)
		elif tok.matches(TT_KEYWORD, 'for'):
			for_expr = res.register(self.for_expr())
			if res.error: return res
			return res.success(for_expr)
		elif tok.matches(TT_KEYWORD, 'while'):
			while_expr = res.register(self.while_expr())
			if res.error: return res
			return res.success(while_expr)
		elif tok.matches(TT_KEYWORD, 'func'):
			func_def = res.register(self.func_def())
			if res.error: return res
			return res.success(func_def)

		return res.failure(InvalidSyntaxError(
			tok.pos_start, tok.pos_end,
			"Expected integer, decimal, identifier, '+', '-', '(', '()', 'if', 'for', 'while' or 'func'"
		))

	def list_expr(self):
		res = ParseResult()
		element_nodes = []
		pos_start = self.current_tok.pos_start.copy()

		if self.current_tok.type != TT_LPAREN:
			return res.failure(
				InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected '('"
				)
			)

		res.register_advancement()
		self.advance()

		if self.current_tok.type == TT_RPAREN:
			res.register_advancement()
			self.advance()
		else:
			expr = res.register(self.expr())
			element_nodes.append(expr)
			if res.error:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected ')', 'if', 'for', 'while', 'func', integer, decimal, identifier, '+', '-', '(', or 'not'"
				))

			if self.current_tok.type != TT_COMMA:
				if self.current_tok.type == TT_RPAREN:
					res.register_advancement()
					self.advance()
					return res.success(expr)
				else:
					return res.failure(InvalidSyntaxError(
						self.current_tok.pos_start, self.current_tok.pos_end,
						"Expected ')' or ','"
					))

			while self.current_tok.type == TT_COMMA:
				res.register_advancement()
				self.advance()

				if self.current_tok.type == TT_RPAREN: break

				element_nodes.append(res.register(self.expr()))
				if res.error: return res

			if self.current_tok.type != TT_RPAREN:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected ',' or ')'"
				))

			res.register_advancement()
			self.advance()
		
		return res.success(ListNode(
			element_nodes,
			pos_start,
			self.current_tok.pos_end.copy()
		))

	def call(self):
		res = ParseResult()
		atom = res.register(self.atom())
		if res.error: return res

		if self.current_tok.type == TT_LPAREN:
			res.register_advancement()
			self.advance()
			arg_nodes = []

			if self.current_tok.type == TT_RPAREN:
				res.register_advancement()
				self.advance()
			else:
				arg_nodes.append(res.register(self.expr()))
				if res.error:
					return res.failure(InvalidSyntaxError(
						self.current_tok.pos_start, self.current_tok.pos_end,
						"Expected ')', 'if', 'for', 'while', 'func', integer, decimal, identifier, '+', '-', '(' or 'not'"
					))

				while self.current_tok.type == TT_COMMA:
					res.register_advancement()
					self.advance()

					arg_nodes.append(res.register(self.expr()))
					if res.error: return res

				if self.current_tok.type != TT_RPAREN:
					return res.failure(InvalidSyntaxError(
						self.current_tok.pos_start, self.current_tok.pos_end,
						"Expected ',' or ')'"
					))

				res.register_advancement()
				self.advance()
			
			return res.success(CallNode(atom, arg_nodes))
		return res.success(atom)

	def power(self):
		return self.bin_op(self.call, (TT_POW, ), self.factor)

	def factor(self):
		res = ParseResult()
		tok = self.current_tok

		if tok.type in (TT_PLUS, TT_MINUS):
			res.register_advancement()
			self.advance()
			factor = res.register(self.factor())
			if res.error: return res
			return res.success(UnaryOpNode(tok, factor))

		return self.power()

	def term(self):
		return self.bin_op(self.factor, (TT_MUL, TT_DIV))

	def arith_expr(self):
		return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

	def comp_expr(self):
		res = ParseResult()

		if self.current_tok.matches(TT_KEYWORD, 'not'):
			op_tok = self.current_tok

			res.register_advancement()
			self.advance()

			node = res.register(self.comp_expr())
			if res.error: return res
			return res.success(UnaryOpNode(op_tok, node))

		node = res.register(self.bin_op(self.arith_expr, (TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE)))

		if res.error:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				"Expected integer, decimal, identifier, '+', '-', '(' or 'not'"
			))

		return res.success(node)

	def expr(self):
		res = ParseResult()

		if self.current_tok.type ==  TT_IDENTIFIER:
			var_name = self.current_tok
			res.register_advancement()
			self.advance()

			if self.current_tok.type != TT_EQ:
				res.register_advancement(-1)
				self.advance(-1)
				node = res.register(self.bin_op(self.comp_expr, ((TT_KEYWORD, 'and'), (TT_KEYWORD, 'or'))))
				if res.error:
					return res.failure(InvalidSyntaxError(
						self.current_tok.pos_start, self.current_tok.pos_end,
						"Expected 'if', 'for', 'while', 'func', integer, decimal, identifier, '+', '-', '(' or 'not'"
					))

				return res.success(node)

			res.register_advancement()
			self.advance()
			expr = res.register(self.expr())
			if res.error: return res

			return res.success(VarAssignNode(var_name, expr))
		elif self.current_tok.matches(TT_KEYWORD, 'pass') or (self.current_tok.type, len(self.tokens)) == (TT_EOF, 1):
			tok = self.current_tok

			res.register_advancement()
			self.advance()

			return res.success(PassNode(tok.pos_start, tok.pos_end))

		node = res.register(self.bin_op(self.comp_expr, ((TT_KEYWORD, 'and'), (TT_KEYWORD, 'or'))))
		if res.error:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				"Expected 'if', 'for', 'while', 'func', integer, decimal, identifier, '+', '-', '(' or 'not'"
			))

		return res.success(node)

	def func_def(self):
		res = ParseResult()

		if not self.current_tok.matches(TT_KEYWORD, 'func'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				"Expected 'func'"
			))

		res.register_advancement()
		self.advance()

		if self.current_tok.type == TT_IDENTIFIER:
			var_name_tok = self.current_tok
			res.register_advancement()
			self.advance()

			if self.current_tok.type != TT_LPAREN:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected '('"
				))
		else:
			var_name_tok = None
			
			if self.current_tok.type != TT_LPAREN:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected identifier or '('"
				))

		res.register_advancement()
		self.advance()
		arg_name_toks = []

		if self.current_tok.type == TT_IDENTIFIER:
			arg_name = self.current_tok
			res.register_advancement()
			self.advance()

			if self.current_tok.type != TT_EQ:
				arg_name_toks.append(arg_name)
			else:
				res.register_advancement()
				self.advance()
				arg_name_toks.append((arg_name, res.register(self.expr())))
				if res.error: return res

			while self.current_tok.type == TT_COMMA:
				res.register_advancement()
				self.advance()

				if self.current_tok.type != TT_IDENTIFIER:
					return res.failure(InvalidSyntaxError(
						self.current_tok.pos_start, self.current_tok.pos_end,
						"Expected identifier"
					))

				arg_name = self.current_tok
				res.register_advancement()
				self.advance()

				if self.current_tok.type != TT_EQ:
					arg_name_toks.append(arg_name)
				else:
					res.register_advancement()
					self.advance()
					arg_name_toks.append((arg_name, res.register(self.expr())))
					if res.error: return res

			if self.current_tok.type not in (TT_RPAREN, TT_EQ):
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected ',' or ')'"
				))
		else:
			if self.current_tok.type != TT_RPAREN:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected identifier or ')'"
				))

		res.register_advancement()
		self.advance()

		if self.current_tok.type == TT_ARROW:
			res.register_advancement()
			self.advance()
			node_to_return = res.register(self.expr())
			if res.error: return res

			return res.success(FuncDefNode(
				var_name_tok,
				arg_name_toks,
				node_to_return,
				True
			))

		if self.current_tok.type != TT_NEWLINE:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected '=>', ';' or new line"
			))

		res.register_advancement()
		self.advance()

		body = res.register(self.statements())
		if res.error: return res

		if not self.current_tok.matches(TT_KEYWORD, 'end'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected 'end'"
			))

		res.register_advancement()
		self.advance()
		
		return res.success(FuncDefNode(
			var_name_tok,
			arg_name_toks,
			body,
			False
		))

	######################################################

	def bin_op(self, func_a, ops, func_b=None, left_value=None, right_value=None):
		if func_b is None:
			func_b = func_a
		
		res = ParseResult()
		left = left_value if left_value is not None else res.register(func_a())
		if res.error: return res

		while self.current_tok.type in ops or (self.current_tok.type, self.current_tok.value) in ops:
			op_tok = self.current_tok
			res.register_advancement()
			self.advance()
			right = right_value if right_value is not None else res.register(func_b())
			if res.error: return res
			left = BinOpNode(left, op_tok, right)

		return res.success(left)

##########################################################
# RUNTIME RESULT
##########################################################

class RTResult:
	def __init__(self):
		self.reset()

	def reset(self):
		self.value = None
		self.error = None
		self.func_return_value = None
		self.loop_should_continue = False
		self.loop_should_break = False

	def register(self, res):
		self.error = res.error
		self.func_return_value = res.func_return_value
		self.loop_should_continue = res.loop_should_continue
		self.loop_should_break = res.loop_should_break
		return res.value

	def success(self, value):
		self.reset()
		self.value = value
		return self

	def success_return(self, value):
		self.reset()
		self.func_return_value = value
		return self
	
	def success_continue(self):
		self.reset()
		self.loop_should_continue = True
		return self
	
	def success_break(self):
		self.reset()
		self.loop_should_break = True
		return self
	
	def failure(self, error):
		self.reset()
		self.error = error
		return self

	def should_return(self):
		return (
			self.error or
			self.func_return_value or
			self.loop_should_continue or
			self.loop_should_break
		)

##########################################################
# VALUES
##########################################################

class Value:
	def __init__(self):
		self.set_pos()
		self.set_context()

	def set_pos(self, pos_start=None, pos_end=None):
		self.pos_start = pos_start
		self.pos_end = pos_end
		return self

	def set_context(self, context=None):
		self.context = context
		return self

	def added_to(self, other):
		return None, self.illegal_operation('+', other)

	def subbed_by(self, other):
		return None, self.illegal_operation('-', other)

	def multed_by(self, other):
		return None, self.illegal_operation('*', other)

	def dived_by(self, other):
		return None, self.illegal_operation('/', other)

	def powed_by(self, other):
		return None, self.illegal_operation('^', other)

	def subscred_by(self, other):
		return None, self.illegal_operation('_', other)

	def get_comparison_eq(self, other):
		return None, self.illegal_operation('==', other)

	def get_comparison_ne(self, other):
		return None, self.illegal_operation('!=', other)

	def get_comparison_lt(self, other):
		return None, self.illegal_operation('<', other)

	def get_comparison_gt(self, other):
		return None, self.illegal_operation('>', other)

	def get_comparison_lte(self, other):
		return None, self.illegal_operation('<=', other)

	def get_comparison_gte(self, other):
		return None, self.illegal_operation('>=', other)

	def anded_by(self, other):
		return None, self.illegal_operation('and', other)

	def ored_by(self, other):
		return None, self.illegal_operation('or', other)

	def notted(self):
		return Boolean, self.illegal_operation('not')

	def execute(self, args):
		return RTResult().failure(self.illegal_operation('call'))

	def copy(self):
		raise Exception('No copy method defined')

	def is_true(self):
		return False

	def illegal_operation(self, op=None, other=None):
		if op is not None:
			if other is None:
				return RTError(
					self.pos_start, self.pos_end,
					f'Illegal operation "{op}" for {self.__class__.__name__}',
					self.context
				)
			return RTError(
				self.pos_start, other.pos_end,
				f'Illegal operation "{op}" between {self.__class__.__name__} and {other.__class__.__name__}',
				self.context
			)
		if other is None: other = self
		return RTError(
			self.pos_start, other.pos_end,
			f'Illegal operation',
			self.context
		)

class Integer(Value):
	def __init__(self, value):
		super().__init__()
		self.value = int(value)

	def added_to(self, other):
		if isinstance(other, (Integer, Boolean)):
			return Integer(self.value + other.value).set_context(self.context), None
		elif isinstance(other, Decimal):
			return Decimal(self.value + other.value).set_context(self.context), None
		elif isinstance(other, Complex):
			return Complex((self.value) + other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '+', other)

	def subbed_by(self, other):
		if isinstance(other, (Integer, Boolean)):
			return Integer(self.value - other.value).set_context(self.context), None
		elif isinstance(other, Decimal):
			return Decimal(self.value - other.value).set_context(self.context), None
		elif isinstance(other, Complex):
			return Complex(self.value - other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '-', other)

	def multed_by(self, other):
		if isinstance(other, (Integer, Boolean)):
			return Integer(self.value * other.value).set_context(self.context), None
		elif isinstance(other, Decimal):
			return Decimal(self.value * other.value).set_context(self.context), None
		elif isinstance(other, Complex):
			return Complex(self.value * other.value).set_context(self.context), None
		elif isinstance(other, String):
			return String(self.value * other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '*', other)

	def dived_by(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex)):
			if other.value == 0:
				return None, RTError(
					other.pos_start, other.pos_end,
					"Division by zero (cause undefined, it approach -inf when we're approaching 0 from the negative and it approach +inf when we're approaching 0 from the positive)",
					self.context
				)

			if isinstance(other, Boolean):
				return Integer(self.value / other.value).set_context(self.context), None
			elif isinstance(other, Complex):
				return Complex(self.value / other.value).set_context(self.context), None
			return Decimal(self.value / other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '/', other)

	def powed_by(self, other):
		if isinstance(other, (Integer, Decimal)):
			if self.value < 0:
				return Complex(self.value ** other.value).set_context(self.context), None
			return other.__class__(self.value ** other.value).set_context(self.context), None
		elif isinstance(other, Boolean):
			return Integer(self.value ** other.value).set_context(self.context), None
		elif isinstance(other, Complex):
			return Complex(self.value ** other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '^', other)
			
	def get_comparison_eq(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List)):
			return Boolean(int(self.value == other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '==', other)

	def get_comparison_ne(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List)):
			return Boolean(int(self.value != other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '!=', other)

	def get_comparison_lt(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value < other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '>', other)

	def get_comparison_gt(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value > other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '<', other)

	def get_comparison_lte(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value <= other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '>=', other)

	def get_comparison_gte(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value >= other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '<=', other)

	def anded_by(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, NullType)):
			class_ = self.__class__ if (self.value and other.value) == self else other.__class__
			return class_(self.value and other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, 'and', other)

	def ored_by(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, NullType)):
			class_ = self.__class__ if (self.value and other.value) == self else other.__class__
			return class_(self.value or other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, 'or', other)

	def notted(self):
		return Boolean(1 if self.value == 0 else 0).set_context(self.context), None

	def copy(self):
		copy = Integer(self.value)
		copy.set_pos(self.pos_start, self.pos_end)
		copy.set_context(self.context)

		return copy

	def is_true(self):
		return self.value != 0

	def __repr__(self):
		return f'{self.value}'

class Decimal(Value):
	def __init__(self, value):
		super().__init__()
		self.value = mpf(str(value))

	def added_to(self, other):
		if isinstance(other, (Integer, Decimal, Boolean)):
			return Decimal(self.value + other.value).set_context(self.context), None
		elif isinstance(other, Complex):
			return Complex(self.value + other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '+', other)

	def subbed_by(self, other):
		if isinstance(other, (Integer, Decimal, Boolean)):
			return Decimal(self.value - other.value).set_context(self.context), None
		elif isinstance(other, Complex):
			return Complex(self.value - other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '-', other)

	def multed_by(self, other):
		if isinstance(other, (Integer, Decimal, Boolean)):
			return Decimal(self.value * other.value).set_context(self.context), None
		elif isinstance(other, Complex):
			return Complex(self.value * other.value).set_context(self.context), None
		elif isinstance(other, String):
			return String(self.value * other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '*', other)

	def dived_by(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex)):
			if other.value == 0:
				return None, RTError(
					other.pos_start, other.pos_end,
					"Division by zero (cause undefined, it approach -inf when we're approaching 0 from the negative and it approach +inf when we're approaching 0 from the positive)",
					self.context
				)
			
			if isinstance(other, Boolean):
				return Integer(self.value / other.value).set_context(self.context), None
			if isinstance(other, Complex):
				return Complex(self.value / other.value).set_context(self.context), None
			return Decimal(self.value / other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '/', other)

	def powed_by(self, other):
		if isinstance(other, (Integer, Decimal, Complex)):
			if self.value < 0 or isinstance(other, Complex):
				return Complex(self.value ** other.value).set_context(self.context), None
			return Decimal(self.value ** other.value).set_context(self.context), None
		elif isinstance(other, Boolean):
			return Decimal(self.value ** other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '^', other)
			
	def get_comparison_eq(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value == other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '==', other)

	def get_comparison_ne(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value != other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '!=', other)

	def get_comparison_lt(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value < other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '>', other)

	def get_comparison_gt(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value > other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '<', other)

	def get_comparison_lte(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value <= other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '>=', other)

	def get_comparison_gte(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value >= other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '<=', other)

	def anded_by(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, NullType)):
			class_ = self.__class__ if (self.value and other.value) == self else other.__class__
			return class_(self.value and other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, 'and', other)

	def ored_by(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, NullType)):
			class_ = self.__class__ if (self.value and other.value) == self else other.__class__
			return class_(self.value or other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, 'or', other)

	def notted(self):
		return Boolean(1 if self.value == 0 else 0).set_context(self.context), None

	def copy(self):
		copy = Decimal(self.value)
		copy.set_pos(self.pos_start, self.pos_end)
		copy.set_context(self.context)

		return copy

	def is_true(self):
		return self.value != 0

	def __repr__(self):
		return f'{self.value}'

class Complex(Value):
	def __init__(self, value):
		super().__init__()
		if not isinstance(value, mpc):
			value = complex(value)
		self.value = mpc(str(float(value.real)), str(float(value.imag)))

	def added_to(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex)):
			return Complex(self.value + other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '+', other)

	def subbed_by(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex)):
			return Complex(self.value - other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '-', other)

	def multed_by(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex)):
			return Complex(self.value * other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '*', other)

	def dived_by(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex)):
			if other.value == 0:
				return None, RTError(
					other.pos_start, other.pos_end,
					"Division by zero (cause undefined, it approach -inf when we're approaching 0 from the negative and it approach +inf when we're approaching 0 from the positive)",
					self.context
				)
			return Complex(self.value / other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '/', other)

	def powed_by(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex)):
			return Complex(self.value ** other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '^', other)
			
	def get_comparison_eq(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value == other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '==', other)

	def get_comparison_ne(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value != other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '!=', other)

	def get_comparison_lt(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value < other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '>', other)

	def get_comparison_gt(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value > other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '<', other)

	def get_comparison_lte(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value <= other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '>=', other)

	def get_comparison_gte(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value >= other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '<=', other)

	def anded_by(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, NullType)):
			class_ = self.__class__ if (self.value and other.value) == self else other.__class__
			return class_(self.value and other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, 'and', other)

	def ored_by(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, NullType)):
			class_ = self.__class__ if (self.value and other.value) == self else other.__class__
			return class_(self.value or other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, 'or', other)

	def notted(self):
		return Boolean(1 if self.value == 0 else 0).set_context(self.context), None

	def copy(self):
		copy = Complex(self.value)
		copy.set_pos(self.pos_start, self.pos_end)
		copy.set_context(self.context)

		return copy

	def is_true(self):
		return self.value != 0

	def __repr__(self):
		return f'{self.value}'.replace('j', 'i')

class Boolean(Value):
	def __init__(self, value):
		super().__init__()
		self.value = False if value == 0 else True

	def added_to(self, other):
		if isinstance(other, (Integer, Boolean)):
			return Integer(self.value + other.value).set_context(self.context), None
		elif isinstance(other, Decimal):
			return Decimal(self.value + other.value).set_context(self.context), None
		elif isinstance(other, Complex):
			return Complex(self.value + other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '+', other)

	def subbed_by(self, other):
		if isinstance(other, (Integer, Boolean)):
			return Integer(self.value - other.value).set_context(self.context), None
		elif isinstance(other, Decimal):
			return Decimal(self.value - other.value).set_context(self.context), None
		elif isinstance(other, Complex):
			return Complex(self.value - other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '-', other)

	def multed_by(self, other):
		if isinstance(other, (Integer, Boolean)):
			return Integer(self.value * other.value).set_context(self.context), None
		elif isinstance(other, Decimal):
			return Decimal(self.value * other.value).set_context(self.context), None
		elif isinstance(other, Complex):
			return Complex(self.value * other.value).set_context(self.context), None
		elif isinstance(other, String):
			return String(self.value * other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '*', other)

	def dived_by(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex)):
			if other.value == 0:
				return None, RTError(
					other.pos_start, other.pos_end,
					"Division by zero (cause undefined, it approach -inf when we're approaching 0 from the negative and it approach +inf when we're approaching 0 from the positive)",
					self.context
				)

			if isinstance(other, Complex):
				return Complex(self.value / other.value).set_context(self.context), None
			return Decimal(self.value / other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '/', other)

	def powed_by(self, other):
		if isinstance(other, (Integer, Boolean)):
			return Integer(self.value ** other.value).set_context(self.context), None
		elif isinstance(other, Decimal):
			return Decimal(self.value ** other.value).set_context(self.context), None
		elif isinstance(other, Complex):
			return Complex(self.value ** other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '^', other)
			
	def get_comparison_eq(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value == other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '==', other)

	def get_comparison_ne(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value != other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '!=', other)

	def get_comparison_lt(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value < other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '>', other)

	def get_comparison_gt(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value > other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '<', other)

	def get_comparison_lte(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value <= other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '>=', other)

	def get_comparison_gte(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value >= other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '<=', other)

	def anded_by(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, NullType)):
			class_ = self.__class__ if (self.value and other.value) == self else other.__class__
			return class_(self.value and other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, 'and', other)

	def ored_by(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, NullType)):
			class_ = self.__class__ if (self.value and other.value) == self else other.__class__
			return class_(self.value or other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, 'or', other)

	def notted(self):
		return Boolean(1 if self.value == 0 else 0).set_context(self.context), None

	def copy(self):
		copy = Boolean(self.value)
		copy.set_pos(self.pos_start, self.pos_end)
		copy.set_context(self.context)

		return copy

	def is_true(self):
		return self.value != 0

	def __repr__(self):
		return f'{'false' if self.value == 0 else 'true'}'

class NullType(Value):
	def __init__(self, value = None):
		super().__init__()
		self.value = value or 'null'
		self.hidden = value is None

	def get_comparison_eq(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, NullType, String, List)):
			return Boolean(0 if not isinstance(other, NullType) else 1).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '==', other)

	def get_comparison_ne(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, NullType, String, List)):
			return Boolean(1 if not isinstance(other, NullType) else 0).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '!=', other)

	def anded_by(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, NullType)):
			return other.__class__(other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, 'and', other)

	def ored_by(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, NullType)):
			return other.__class__(other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, 'or', other)

	def notted(self):
		return Boolean(1), None

	def copy(self):
		copy = NullType(self.value)
		copy.set_pos(self.pos_start, self.pos_end)
		copy.set_context(self.context)

		return copy

	def is_true(self):
		return False
	
	def __repr__(self):
		return f'{self.value}'

class String(Value):
	def __init__(self, value):
		super().__init__()
		self.value = value

	def added_to(self, other):
		if isinstance(other, String):
			return String(self.value + other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '+', other)

	def multed_by(self, other):
		if isinstance(other, (Integer, Boolean)):
			return String(self.value * other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '*', other)
			
	def subscred_by(self, other):
		if isinstance(other, (Integer, Boolean)):
			try:
				return String(self.value[other.value]), None
			except:
				return None, RTError(
					other.pos_start, other.pos_end,
					'Character at this index could not be retrived from string because index is out of bounds',
					self.context
				)
		else:
			return None, Value.illegal_operation(self, '_', other)

	def get_comparison_eq(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value == other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '==', other)

	def get_comparison_ne(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value != other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '!=', other)

	def get_comparison_lt(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value > other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '>', other)

	def get_comparison_gt(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value < other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '<', other)

	def get_comparison_lte(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value >= other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '>=', other)

	def get_comparison_gte(self, other):
		if isinstance(other, (Integer, Decimal, Boolean, Complex, String, List, NullType)):
			return Boolean(int(self.value <= other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, '<=', other)
		
	def notted(self):
		return Boolean(1 if len(self.value) == 0 else 0).set_context(self.context), None

	def is_true(self):
		return len(self.value) > 0

	def copy(self):
		copy = String(self.value)
		copy.set_pos(self.pos_start, self.pos_end)
		copy.set_context(self.context)
		return copy

	def __repr__(self):
		return repr(self.value)
	
	def __str__(self):
		return self.value

class List(Value):
	def __init__(self, elements):
		super().__init__()
		self.elements = elements

	def added_to(self, other):
		if isinstance(other, List):
			new_list = self.copy()
			new_list.elements += other.elements
			return new_list, None
		else:
			return None, Value.illegal_operation(self, '+', other)

	def subbed_by(self, other):
		if isinstance(other, (Integer, Boolean)):
			new_list = self.copy()
			try:
				new_list.elements.pop(other.value)
				return new_list, None
			except:
				return None, RTError(
					other.pos_start, other.pos_end,
					'Element at this index could not be removed from list because index is out of bounds',
					self.context
				)
		else:
			return None, Value.illegal_operation(self, '-', other)

	def multed_by(self, other):
		if isinstance(other, List):
			new_list = self.copy()
			new_list.elements.extend(other.elements)
			return new_list, None
		elif isinstance(other, Integer):
			return List(self.copy().elements * other.value), None
		else:
			return None, Value.illegal_operation(self, '*', other)

	def subscred_by(self, other):
		if isinstance(other, (Integer, Boolean)):
			try:
				return self.elements[other.value], None
			except:
				return None, RTError(
					other.pos_start, other.pos_end,
					'Element at this index could not be retrived from list because index is out of bounds',
					self.context
				)
		else:
			return None, Value.illegal_operation(self, '_', other)

	def __repr__(self):
		if len(self.elements) == 0:
			return '()'
		return f"({repr(self.elements[0])},{','.join(' ' + repr(x) for x in self.elements[1:])})"

	def copy(self):
		copy = List(self.elements)
		copy.set_pos(self.pos_start, self.pos_end)
		copy.set_context(self.context)

		return copy
	
class BaseFunction(Value):
	def __init__(self, name):
		super().__init__()
		self.name = name or '<anonymous>'
	
	def generate_new_context(self):
		new_context = Context(self.name, self.context, self.pos_start)
		new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)

		return new_context
	
	def check_args(self, arg_names, args):
		res = RTResult()

		if len(args) > len(arg_names):
			return res.failure(RTError(
				self.pos_start, self.pos_end,
				f"{len(args) - len(arg_names)} too many args passed into '{self.name}'",
				self.context
			))
		
		if len(args) < len(arg_names):
			return res.failure(RTError(
				self.pos_start, self.pos_end,
				f"{len(arg_names) - len(args)} too few args passed into '{self.name}'",
				self.context
			))
		
		return res.success(None)
	
	def populate_args(self, arg_names, args, exec_ctx):
		for i in range(len(args[0])):
			arg_name = arg_names[0][i]
			arg_value = args[0][i]
			if isinstance(arg_value, type(None)): arg_value = NullType()
			arg_value.set_context(exec_ctx)
			exec_ctx.symbol_table.set(arg_name, arg_value)

		opt_arg_names = arg_names[1].copy()

		for arg_name, arg_value in args[1].items():
			if isinstance(arg_value, type(None)): arg_value = NullType()
			arg_value.set_context(exec_ctx)
			opt_arg_names[arg_name] = arg_value

		for arg_name, arg_value in opt_arg_names.items():
			exec_ctx.symbol_table.set(arg_name, arg_value)

		if debug_mode == debug_modes_list[3]:
			print(f"Args passed to {self.name}: {exec_ctx.symbol_table}")

	def check_and_populate_args(self, arg_names, args, exec_ctx):
		res = RTResult()

		if debug_mode == debug_modes_list[3]:
			print(f"Args of {self.name}: {exec_ctx.symbol_table}")

		res.register(self.check_args(arg_names[0], args[0]))
		if res.should_return(): return res
		self.populate_args(arg_names, args, exec_ctx)

		return res.success(None)

class Function(BaseFunction):
	def __init__(self, name, body_node, arg_names, should_auto_return):
		super().__init__(name)
		self.body_node = body_node
		self.arg_names = arg_names
		self.should_auto_return = should_auto_return
	
	def execute(self, args):
		res = RTResult()
		interpreter = Interpreter()
		exec_ctx = self.generate_new_context()

		res.register(self.check_and_populate_args(self.arg_names, args, exec_ctx))
		if res.should_return(): return res

		value = res.register(interpreter.visit(self.body_node, exec_ctx))
		if res.should_return() and res.func_return_value is None: return res

		ret_value = (value if self.should_auto_return else None) or res.func_return_value or NullType()
		return res.success(ret_value)

	def copy(self):
		copy = Function(self.name, self.body_node, self.arg_names, self.should_auto_return)
		copy.set_context(self.context)
		copy.set_pos(self.pos_start, self.pos_end)
		return copy

	def __repr__(self):
		return f"<function {self.name}>"
	
class BuiltInFunction(BaseFunction):
	def __init__(self, name):
		super().__init__(name)
	
	def execute(self, args):
		res = RTResult()
		exec_ctx = self.generate_new_context()

		method_name = f'execute_{self.name}'
		method = getattr(self, method_name, self.no_visit_method)

		res.register(self.check_and_populate_args((method.positional_arg_names, method.optional_arg_names), args, exec_ctx))
		if res.should_return(): return res

		return_value = res.register(method(exec_ctx))
		if res.should_return(): return res

		return res.success(return_value)

	def no_visit_method(self, node, context):
		raise NameError(f'No execute_{self.name} method defined')
	
	def copy(self):
		copy = BuiltInFunction(self.name)
		copy.set_context(self.context)
		copy.set_pos(self.pos_start, self.pos_end)
		return copy
	
	def __repr__(self):
		return f'<built-in function {self.name}>'
	
	######################################################

	def execute_print(self, exec_ctx):
		value = exec_ctx.symbol_table.get('value')
		sep = exec_ctx.symbol_table.get('sep')
		end_char = exec_ctx.symbol_table.get('end_char')

		if isinstance(end_char, NullType):
			end_char = '\n'
		end_char = str(end_char)

		if isinstance(value, List) and not isinstance(sep, NullType):
			print(str(sep).join(str(x) for x in value.elements), end=end_char)
		else:
			print(str(value), end=end_char)

		return RTResult().success(NullType())
	execute_print.positional_arg_names = ["value"] # type: ignore
	execute_print.optional_arg_names = {"sep": NullType(), "end_char": NullType()} # type: ignore

	def execute_input(self, exec_ctx):
		placeholder = exec_ctx.symbol_table.get('placeholder')
		if isinstance(placeholder, NullType): text = input()
		else: text = input(placeholder)
		return RTResult().success(String(text))
	execute_input.positional_arg_names = [] # type: ignore
	execute_input.optional_arg_names = {"placeholder": NullType()} # type: ignore

	def execute_clear(self, exec_ctx):
		print('\033c')
		return RTResult().success(NullType())
	execute_clear.positional_arg_names = [] # type: ignore
	execute_clear.optional_arg_names = {} # type: ignore

	def execute_exit(self, exec_ctx):
		code = exec_ctx.symbol_table.get('code')
		if not isinstance(code, NullType):
			print("Exited:", code)
			sys.exit(code)
		sys.exit()
	execute_exit.positional_arg_names = [] # type: ignore
	execute_exit.optional_arg_names = {"code": NullType()} # type: ignore

	def execute_type(self, exec_ctx):
		obj = exec_ctx.symbol_table.get('obj')
		return RTResult().success(String(obj.__class__.__name__))
	execute_type.positional_arg_names = ["obj"] # type: ignore
	execute_type.optional_arg_names = {} # type: ignore

	def execute_sin(self, exec_ctx):
		theta = exec_ctx.symbol_table.get('theta')
		e = global_symbol_table.get('e')
		return RTResult().success(Complex((e.value ** (1j * theta.value) - e.value ** (-1j * theta.value)) / 2j))
	execute_sin.positional_arg_names = ["theta"] # type: ignore
	execute_sin.optional_arg_names = {} # type: ignore

	def execute_cos(self, exec_ctx):
		theta = exec_ctx.symbol_table.get('theta')
		e = global_symbol_table.get('e')
		return RTResult().success(Complex((e.value ** (1j * theta.value) + e.value ** (-1j * theta.value)) / 2))
	execute_cos.positional_arg_names = ["theta"] # type: ignore
	execute_cos.optional_arg_names = {} # type: ignore

	def execute_exec(self, exec_ctx):
		code_or_filename = exec_ctx.symbol_table.get('code_or_filename')
		
		if not isinstance(code_or_filename, String):
			return RTResult.failure(RTError(
				self.pos_start, self.pos_end,
				"Argument code_or_filename must be a String.",
				exec_ctx
			))

		code_or_filename = code_or_filename.value
		is_filename = re.match('((^([a-z]|[A-Z]):(?=\\(?![\0-\37<>:"/\\|?*])|\/(?![\0-\37<>:"/\\|?*])|$)|^\\(?=[\\\/][^\0-\37<>:"/\\|?*]+)|^(?=(\\|\/)$)|^\.(?=(\\|\/)$)|^\.\.(?=(\\|\/)$)|^(?=(\\|\/)[^\0-\37<>:"/\\|?*]+)|^\.(?=(\\|\/)[^\0-\37<>:"/\\|?*]+)|^\.\.(?=(\\|\/)[^\0-\37<>:"/\\|?*]+))((\\|\/)[^\0-\37<>:"/\\|?*]+|(\\|\/)$)*()$)|(^\/$|(^(?=\/)|^\.|^\.\.)(\/(?=[^/\0])[^/\0]+)*\/?$)', code_or_filename)
		filename = code_or_filename if is_filename else '<code>'
		
		if is_filename:
			try:
				with open(filename, 'r') as file:
					code = file.read()
			except Exception as e:
				return RTResult().failure(RTError(
					self.pos_start, self.pos_end,
					f'Failed to open file "{filename}" because of the following exception:\n{e}',
					exec_ctx
				))
		else:
			code = code_or_filename

		_, error = run(filename, code)

		if error:
			return RTResult().failure(RTError(
				self.pos_start, self.pos_end,
				f'Failed to run "{filename}" because of the following exception:\n{error}',
				exec_ctx
			))
		
		return RTResult().success(NullType())
	execute_run.positional_arg_names = ["code_or_filename"] # type: ignore
	execute_run.optional_arg_names = {} # type: ignore

	def execute_length(self, exec_ctx):
		iterable = exec_ctx.symbol_table.get('iterable')

		if not isinstance(iterable, (List, String)):
			return RTResult().failure(RTError(
				self.pos_start, self.pos_end,
				"Argument iterable must be a List or a String.",
				exec_ctx
			))

		return RTResult().success(Integer(
			len(iterable.elements if isinstance(iterable, List) else iterable.value)
		))
	execute_length.positional_arg_names = ["iterable"] # type: ignore
	execute_length.optional_arg_names = {} # type: ignore

##########################################################
# CONTEXT
##########################################################

class Context:
	def __init__(self, display_name, parent=None, parent_entry_pos=None):
		self.display_name = display_name
		self.parent = parent
		self.parent_entry_pos = parent_entry_pos
		self.symbol_table = None

##########################################################
# SYMBOL TABLE
##########################################################

class SymbolTable:
	def __init__(self, parent=None):
		self.symbols = {}
		self.parent = parent

	def get(self, name):
		value = self.symbols.get(name, None)
		if value is None and self.parent:
			return self.parent.get(name)
		return value

	def set(self, name, value):
		self.symbols[name] = value

	def remove(self, name):
		del self.symbols[name]
	
	def __repr__(self):
		return f'SymbolTable{self.symbols}'

##########################################################
# INTERPRETER
##########################################################

class Interpreter:
	def visit(self, node, context):
		method_name = f'visit_{type(node).__name__}'
		method = getattr(self, method_name, self.no_visit_method)
		return method(node, context)

	def no_visit_method(self, node, context):
		raise Exception(f'No "visit_{type(node).__name__}" method defined')

	######################################################

	def visit_IntegerNode(self, node, context):
		return RTResult().success(
			Integer(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
		)

	def visit_DecimalNode(self, node, context):
		return RTResult().success(
			Decimal(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
		)

	def visit_ComplexNode(self, node, context):
		return RTResult().success(
			Complex(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
		)

	def visit_ListNode(self, node, context):
		res = RTResult()
		elements = []

		for element_node in node.element_nodes:
			elements.append(res.register(self.visit(element_node, context)))
			if res.should_return(): return res

		return res.success(
			List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
		)

	def visit_StringNode(self, node, context):
		return RTResult().success(
			String(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
		)
	
	def visit_PassNode(self, node, context):
		return RTResult().success(NullType())

	def visit_VarAccessNode(self, node, context):
		res = RTResult()
		var_name = node.var_name_tok.value
		value = context.symbol_table.get(var_name)

		if value is None:
			return res.failure(RTError(
				node.pos_start, node.pos_end,
				f"'{var_name}' is not defined",
				context
			))

		value = value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
		return res.success(value)

	def visit_VarAssignNode(self, node, context):
		res = RTResult()
		var_name = node.var_name_tok.value
		value = res.register(self.visit(node.value_node, context))
		if res.should_return(): return res

		context.symbol_table.set(var_name, value)

		return res.success(None)

	def visit_BinOpNode(self, node, context):
		res = RTResult()
		left = res.register(self.visit(node.left_node, context))
		if res.should_return(): return res
		right = res.register(self.visit(node.right_node, context))
		if res.should_return(): return res

		if node.op_tok.type == TT_PLUS:
			result, error = left.added_to(right)
		elif node.op_tok.type == TT_MINUS:
			result, error = left.subbed_by(right)
		elif node.op_tok.type == TT_MUL:
			result, error = left.multed_by(right)
		elif node.op_tok.type == TT_DIV:
			result, error = left.dived_by(right)
		elif node.op_tok.type == TT_POW:
			result, error = left.powed_by(right)
		elif node.op_tok.type == TT_SUBSCRIPT:
			result, error = left.subscred_by(right)
		elif node.op_tok.type == TT_EE:
			result, error = left.get_comparison_eq(right)
		elif node.op_tok.type == TT_NE:
			result, error = left.get_comparison_ne(right)
		elif node.op_tok.type == TT_LT:
			result, error = left.get_comparison_lt(right)
		elif node.op_tok.type == TT_GT:
			result, error = left.get_comparison_gt(right)
		elif node.op_tok.type == TT_LTE:
			result, error = left.get_comparison_lte(right)
		elif node.op_tok.type == TT_GTE:
			result, error = left.get_comparison_gte(right)
		elif node.op_tok.matches(TT_KEYWORD, 'and'):
			result, error = left.anded_by(right)
		elif node.op_tok.matches(TT_KEYWORD, 'or'):
			result, error = left.ored_by(right)

		if error:
			return res.failure(error)
		else:
			return res.success(result.set_pos(node.pos_start, node.pos_end))

	def visit_UnaryOpNode(self, node, context):
		res = RTResult()
		number = res.register(self.visit(node.node, context))
		if res.should_return(): return res

		error = None

		if node.op_tok.type == TT_MINUS:
			if isinstance(number, String):
				return res.failure(RTError(
					node.pos_start, node.pos_end,
					'Illegal operation "-" for String',
					context
				))
			number, error = number.multed_by(Integer(-1))
		elif node.op_tok.matches(TT_KEYWORD, 'not'):
			number, error = number.notted()

		if error:
			return res.failure(error)
		else:
			return res.success(number.set_pos(node.pos_start, node.pos_end))

	def visit_IfNode(self, node, context):
		res = RTResult()

		for condition, expr, should_return_null in node.cases:
			condition_value = res.register(self.visit(condition, context))
			if res.should_return(): return res

			if condition_value.is_true():
				expr_value = res.register(self.visit(expr, context))
				if res.should_return(): return res
				return res.success(None if should_return_null else expr_value)

		if node.else_case:
			expr, should_return_null = node.else_case
			else_value = res.register(self.visit(expr, context))
			if res.should_return(): return res
			return res.success(None if should_return_null else else_value)

		return res.success(None)
	
	def visit_ForNode(self, node, context):
		res = RTResult()
		elements = []

		start_value = res.register(self.visit(node.start_value_node, context))
		if res.should_return(): return res

		end_value = res.register(self.visit(node.end_value_node, context))
		if res.should_return(): return res

		if node.step_value_node:
			step_value = res.register(self.visit(node.step_value_node, context))
			if res.should_return(): return res
		else:
			step_value = Integer(1)

		i = start_value.value

		if step_value.value > 0:
			condition = lambda: i < end_value.value
		elif step_value.value == 0:
			return res.failure(RTError(
				node.end_value_node.pos_end.copy().advance(), node.step_value_node.pos_end,
				'Cannot iterate over sequence with step of zero.', context
			))
		else:
			condition = lambda: i > end_value.value
		
		while condition():
			if isinstance(step_value, Integer):
				context.symbol_table.set(node.var_name_tok.value, Integer(i))
			elif isinstance(step_value, Decimal):
				context.symbol_table.set(node.var_name_tok.value, Decimal(i))
			i += step_value.value

			value = res.register(self.visit(node.body_node, context))
			if res.should_return() and res.loop_should_continue == False and res.loop_should_break == False: return res

			if res.loop_should_continue:
				continue

			if res.loop_should_break:
				break

			elements.append(value or NullType())

		return res.success(
			None if node.should_return_null else 
			List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
		)

	def visit_WhileNode(self, node, context):
		res = RTResult()
		elements = []

		while True:
			condition = res.register(self.visit(node.condition_node, context))
			if res.should_return(): return res

			if not condition.is_true(): break

			value = res.register(self.visit(node.body_node, context))
			if res.should_return() and res.loop_should_continue == False and res.loop_should_break == False: return res

			if res.loop_should_continue:
				continue

			if res.loop_should_break:
				break

			elements.append(value or NullType())

		return res.success(
			None if node.should_return_null else 
			List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
		)

	def visit_FuncDefNode(self, node, context):
		res = RTResult()

		func_name = node.var_name_tok.value if node.var_name_tok is not None else None
		body_node = node.body_node
		arg_names = ([arg_name.value for arg_name in node.arg_name_toks if isinstance(arg_name, Token)],
			   {self.visit(arg[0], context).value if not isinstance(arg[0], Token) else arg[0].value:
	   			self.visit(arg[1], context).value if not isinstance(arg[1], Token) else arg[1].value
				for arg in node.arg_name_toks if not isinstance(arg, Token)})
		func_value = Function(func_name, body_node, arg_names, node.should_auto_return).set_context(context).set_pos(node.pos_start, node.pos_end)

		if node.var_name_tok is not None:
			context.symbol_table.set(func_name, func_value)

		return res.success(None)

	def visit_CallNode(self, node, context):
		res = RTResult()
		pos_args = []
		opt_args = {}

		value_to_call = res.register(self.visit(node.node_to_call, context))
		if res.should_return(): return res
		value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)
		
		for arg_node in node.arg_nodes:
			if not isinstance(arg_node, VarAssignNode):
				pos_args.append(res.register(self.visit(arg_node, context)))
			else:
				opt_args[arg_node.var_name_tok.value] = res.register(self.visit(arg_node.value_node, context))
			
			if res.should_return(): return res

		return_value = res.register(value_to_call.execute((pos_args, opt_args)))
		if res.should_return(): return res
		return_value = return_value.copy().set_pos(node.pos_start, node.pos_end).set_context(context) if return_value is not None else None
		return res.success(return_value)
	
	def visit_ReturnNode(self, node, context):
		res = RTResult()

		if node.node_to_return:
			value = res.register(self.visit(node.node_to_return, context))
			if res.should_return(): return res
		else:
			value = NullType()

		return res.success_return(value)

	def visit_ContinueNode(self, node, context):
		return RTResult().success_continue()

	def visit_BreakNode(self, node, context):
		return RTResult().success_break()

##########################################################
# RUN
##########################################################

global_symbol_table = SymbolTable()
global_symbol_table.set('version', String(f'v{version_str}'))
global_symbol_table.set('null', NullType('null'))
global_symbol_table.set('none', NullType('none'))
global_symbol_table.set('undefined', NullType('undefined'))
global_symbol_table.set('true', Boolean(1))
global_symbol_table.set('false', Boolean(0))
global_symbol_table.set('inf', Decimal(float('inf')))
global_symbol_table.set('nan', Decimal(float('nan')))
global_symbol_table.set('print', BuiltInFunction('print'))
global_symbol_table.set('input', BuiltInFunction('input'))
global_symbol_table.set('clear', BuiltInFunction('clear'))
global_symbol_table.set('exit', BuiltInFunction('exit'))
global_symbol_table.set('type', BuiltInFunction('type'))
global_symbol_table.set('sin', BuiltInFunction('sin'))
global_symbol_table.set('cos', BuiltInFunction('cos'))
global_symbol_table.set('exec', BuiltInFunction('exec'))
global_symbol_table.set('length', BuiltInFunction('length'))
global_symbol_table.set('pi', Decimal(3.14159265358979323846264338327950288419716939937510582097494459230781640628620899862803482534211706798214808651328230664709384460955058223172535940812848111745028410270193852110555964462294895493038196442881097566593344612847564823378678316527120190914564856692346034861045432664821339360726024914127372458700660631558817488152092096282925409171536436789259036001133053054882046652138414695194151160943305727036575959195309218611738193261179310511854807446237996274956735188575272489122793818301194912983367336244065664308602139494639522473719070217986094370277053921717629317675238467481846766940513200056812714526356082778577134275778960917363717872146844090122495343014654958537105079227968925892354201995611212902196086403441815981362977477130996051870721134999999837297804995105973173281609631859502445945534690830264252230825334468503526193118817101000313783875288658753320838142061717766914730359825349042875546873115956286388235378759375195778185778053217122680661300192787661119590921642019893809525720106548586327886593615338182796823030195203530185296899577362259941389124972177528347913151557485724245415069595082953311686172785588907509838175463746493931925506040092770167113900984882401285836160356370766010471018194295559619894676783744944825537977472684710404753464620804668425906949129331367702898915210475216205696602405803815019351125338243003558764024749647326391419927260426992279678235478163600934172164121992458631503028618297455570674983850549458858692699569092721079750930295532116534498720275596023648066549911988183479775356636980742654252786255181841757467289097777279380008164706001614524919217321721477235014144197356854816136115735255213347574184946843852332390739414333454776241686251898356948556209921922218427255025425688767179049460165346680498862723279178608578438382796797668145410095388378636095068006422512520511739298489608412848862694560424196528502221066118630674427862203919494504712371378696095636437191728746776465757396241389086583264599581339047802758995))
global_symbol_table.set('e', Decimal(2.71828182845904523536028747135266249775724709369995957496696762772407663035354759457138217852516642742746639193200305992181741359662904357290033429526059563073813232862794349076323382988075319525101901157383418793070215408914993488416750924476146066808226480016847741185374234544243710753907774499206955170276183860626133138458300075204493382656029760673711320070932870912744374704723069697720931014169283681902551510865746377211125238978442505695369677078544996996794686445490598793163688923009879312773617821542499922957635148220826989519366803318252886939849646510582093923982948879332036250944311730123819706841614039701983767932068328237646480429531180232878250981945581530175671736133206981125099618188159304169035159888851934580727386673858942287922849989208680582574927961048419844436346324496848756023362482704197862320900216099023530436994184914631409343173814364054625315209618369088870701676839642437814059271456354906130310720851038375051011574770417189861068739696552126715468895703503540212340784981933432106817012100562788023519303322474501585390473041995777709350366041699732972508868769664035557071622684471625607988265178713419512466520103059212366771943252786753985589448969709640975459185695638023637016211204774272283648961342251644507818244235294863637214174023889344124796357437026375529444833799801612549227850925778256209262264832627793338656648162772516401910590049164499828931505660472580277863186415519565324425869829469593080191529872117255634754639644791014590409058629849679128740687050489585867174798546677575732056812884592054133405392200011378630094556068816674001698420558040336379537645203040243225661352783695117788386387443966253224985065499588623428189970773327617178392803494650143455889707194258639877275471096295374152111513683506275260232648472870392076431005958411661205452970302364725492966693811513732275364509888903136020572481765851180630364428123149655070475102544650117272115551948668508003685322818315219600373562527944951582841882947876108526398144))

def run(fn, text):
	# Generate tokens
	lexer = Lexer(fn, text)
	tokens, error = lexer.make_tokens()


	if error: return None, error

	# Generate AST
	parser = Parser(tokens)
	ast = parser.parse()

	if debug_mode in [debug_modes_list[x] for x in [0, 2, 3]]:
		print("Lexer:", tokens)
		if error: print("Lexer error:", error.as_string())
	
	if debug_mode in [debug_modes_list[x] for x in [1, 2, 3]]:
		print("Parser:", ast.node)
		if ast.error: print("Parser error:", ast.error.as_string())

	if debug_mode in debug_modes_list[:3]: return None, None
	
	if ast.error: return None, ast.error

	# Run program
	interpreter = Interpreter()
	context = Context('<program>')
	context.symbol_table = global_symbol_table
	result = interpreter.visit(ast.node, context)

	if debug_mode == debug_modes_list[3]:
		if result.value is not None:
			print("Multiline list:", result.value, [repr(x) for x in result.value.elements if x is not None], sep='\n    ')
		else:
			print("Multiline list:", result.value, sep='\n    ')

	return result.value, result.error