
if __name__ == '__main__':

	d = {'a': 0, 'b': 1}
	# Map, filter, and dict methods will be converted to lists.
	for _ in d.keys():
		print(_)

	for _ in filter(lambda x: x > 0, d.keys()):
		print(_)

	for _ in map(lambda x: x + 1, d.keys()):
		print(_)

	# Exceptions out of scope
	for _ in range(2):
		try:
			raise ValueError('Hey!') # Example only
		except ValueError as e:
			print('Attempt {} of 2.'.format(_))
			continue
	print('Failed too many times!')
	# Works in py2, NameError in py3
	raise e

	# Floor division
	result = 1 / 2

	# Prints 0 in py2, 0.5 in py3
	print('The result is: {}'.format(result))
