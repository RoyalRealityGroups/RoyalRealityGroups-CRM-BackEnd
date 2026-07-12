from sly import Lexer
from sly import Parser


class BasicLexer(Lexer):
	tokens = { NAME, FLOAT, NUMBER, STRING, LPAREN, RPAREN }
	ignore = '\t '
	literals = { '=', '+', '-', '/',
	'*', '(', ')', ',', ';'}


	# Define tokens as regular expressions
	# (stored as raw strings)
	NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'
	STRING = r'\".*?\"'
	# DOT     = r'\.'
	LPAREN  = r'\('
	RPAREN  = r'\)'

	# Number token
	@_(r'[0-9]+\.[0-9]*')
	def FLOAT(self, t):

		# convert it into a python float
		t.value = float(t.value)
		return t

	# Number token
	@_(r'\d+')
	def NUMBER(self, t):

		# convert it into a python integer
		t.value = int(t.value)
		return t

	# Comment token
	@_(r'//.*')
	def COMMENT(self, t):
		pass

	# Newline token(used only for showing
	# errors in new line)
	@_(r'\n+')
	def newline(self, t):
		self.lineno = t.value.count('\n')


class BasicParser(Parser):
	#tokens are passed from lexer to parser
	tokens = BasicLexer.tokens
	errors = []

	precedence = (
		('left', '+', '-'),
		('left', '*', '/'),
		('right', 'UMINUS'),
	)

	def __init__(self):
		self.env = { }
		self.errors = []

	@_('')
	def statement(self, p):
		pass

	@_('var_assign')
	def statement(self, p):
		return p.var_assign

	@_('NAME "=" expr')
	def var_assign(self, p):
		return ('var_assign', p.NAME, p.expr)

	@_('NAME "=" STRING')
	def var_assign(self, p):
		return ('var_assign', p.NAME, p.STRING)

	@_('expr')
	def statement(self, p):
		return (p.expr)

	@_('expr "+" expr')
	def expr(self, p):
		return ('add', p.expr0, p.expr1)

	@_('expr "-" expr')
	def expr(self, p):
		return ('sub', p.expr0, p.expr1)

	@_('expr "*" expr')
	def expr(self, p):
		return ('mul', p.expr0, p.expr1)


	@_('expr "/" expr')
	def expr(self, p):
		return ('div', p.expr0, p.expr1)

	@_('"-" expr %prec UMINUS')
	def expr(self, p):
		return p.expr

	# @_('expr DOT')
	# def expr(self, p):
	# 	return ('dot', p.expr)
		
	# @_('expr DOT expr')
	# def expr(self, p):
	# 	print("expr DOT expr called ")
	# 	print("p.expr0: ", p.expr0)
	# 	print("p.expr1: ", p.expr1)
	# 	return ('dot', p.expr0, p.expr1)

	@_('NAME')
	def expr(self, p):
		return ('var', p.NAME)

	@_('NUMBER')
	def expr(self, p):
		return ('num', p.NUMBER)

	@_('FLOAT')
	def expr(self, p):
		return ('float', p.FLOAT)
		
	@_('LPAREN expr RPAREN')
	def expr(self, p):
		return ('group-expression',p.expr)

	def error(self, token):
		'''
		Default error handling function.  This may be subclassed.
		'''
		if token:
			lineno = getattr(token, 'lineno', 0)
			if lineno:
				self.errors.append({"error_msg": f'Syntax error at line {lineno}, token={token.type}\n'})
			else:
				self.errors.append({"error_msg": f'Syntax error, token={token.type}'})
		else:
			self.errors.append({"error_msg": 'Parse error in input. EOF\n'})

class BasicExecute:

	errors = []

	def __init__(self, tree, env):
		self.errors = []
		self.env = env
		self.tree = tree
	
	def execute(self):
		# try:
		result = self.walkTree(self.tree)
		# except Exception as e:
		# 	raise e

		# print("the main result is: ", result)
		# if result is not None and isinstance(result, int):
		# 	print("result is in int and result is: ", result)

		# if result is not None and isinstance(result, float):
		# 	print("result is in float and result is: ", result)
		# if isinstance(result, str) and result[0] == '"':
		# 	print(result)

		if (result is not None and (isinstance(result, int) or isinstance(result, float))):
			return result
		else:
			self.errors.append({"error_msg": "Output is not an integer or float"})
			return None

		

	def walkTree(self, node):
		if isinstance(node, int):
			return node
		if isinstance(node, float):
			return node
		if isinstance(node, str):
			return node

		if node is None:
			return None

		if node[0] == 'program':
			if node[1] == None:
				self.walkTree(node[2])
			else:
				self.walkTree(node[1])
				self.walkTree(node[2])

		if node[0] == 'num':
			return node[1]

		if node[0] == 'float':
			return node[1]

		if node[0] == 'str':
			return node[1]

		if node[0] == 'add':
			return self.walkTree(node[1]) + self.walkTree(node[2])
		elif node[0] == 'sub':
			return self.walkTree(node[1]) - self.walkTree(node[2])
		elif node[0] == 'mul':
			return self.walkTree(node[1]) * self.walkTree(node[2])
		elif node[0] == 'div':
			return self.walkTree(node[1]) / self.walkTree(node[2])


		elif node[0] == 'group-expression':
			return self.walkTree(node[1])

		elif node[0] == 'var_assign':
			self.env[node[1]] = self.walkTree(node[2])
			return node[1]

		elif node[0] == 'var':
			try:
				return self.env[node[1]]
			except LookupError as le:
				self.errors.append({"error_msg": "Lookup Error - Undefined variable, '"+node[1]+"' Not found!"})
				return 0



	
		
def formula_validator(input_data):

	lexer = BasicLexer()
	parser = BasicParser()
	tree = None
	tokens = None
	errors = None

	try:
		tokens = lexer.tokenize(input_data)
	
	except Exception as e:
		errors = [{"error_msg":str(e)}]
		return { 'error': True, 'errors': errors }


	if tokens != None:
		try:
			tree = parser.parse(tokens)
			errors = parser.errors
			if len(errors) == 0 and tree != None:
				return { 'error': False, 'tree': tree, }
			else:
				return { 'error': True, 'errors': errors }
		except Exception as e:
			errors = [{"error_msg":str(e)}]
			return { 'error': True, 'errors': errors }
	else:
		return { 'error': True, 'errors': [{"error_msg":"No tokens Available"}] }



def formula_executer(input_data, env={}):
	res = formula_validator(input_data,)

	if res['error']:
		return res
	else:
		try:
			executer = BasicExecute(res['tree'], env)
			result =executer.execute()
			errors = executer.errors
			if len(errors) == 0 and result != None:
				return { 'error': False, 'errors': errors, 'env': env, 'result': result }
			else:
				return { 'error': True, 'errors': errors }
		except Exception as e:
			errors = [{"error_msg":str(e)}]
			return { 'error': True, 'errors': errors }

			
if __name__ == '__main__':
	input_data = '0.3 + 43.36 + (a +25) * (b - c)+ K'
	env = { 'a': 25,'b': 85, 'c': 2}
	res = formula_validator(input_data)
	# print(res)
	result = formula_executer(input_data, env)
	# print(result)
	if(result['error']):
		print("Errors: ", result['errors'])
	else:
		print("Result: ", result['result'])

	input_data = 'FINANCEAMOUNT*(INTERESTRATE/100'
	env = {"FINANCEAMOUNT":25000,"INTERESTRATE":7,"TENURES":0}
	res = formula_validator(input_data)
	# print(res)
	result = formula_executer(input_data, env)
	print(result)
	if(result['error']):
		print("Errors: ", result['errors'])
	else:
		print("Result: ", result['result'])

	print("AFTER----------------")

	input_data = '(SALEAMOUNT - DOWNPAYMENTAMOUNT)'
	env = {"SALEAMOUNT":55000,"DOWNPAYMENTAMOUNT":1000}
	res = formula_validator(input_data)
	# print(res)
	result = formula_executer(input_data, env)
	print(result)
	if(result['error']):
		print("Errors: ", result['errors'])
	else:
		print("Result: ", result['result'])
