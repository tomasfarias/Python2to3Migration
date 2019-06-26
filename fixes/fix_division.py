from lib2to3 import fixer_base
from lib2to3.fixer_util import Name

class FixDivision(fixer_base.BaseFix):

	BM_compatible = True
	PATTERN = "'/'"

	def transform(self, node, results):
		return Name("//", prefix=node.prefix)
