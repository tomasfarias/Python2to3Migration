## My experience migrating Python 2 to Python 3

I like to imagine my team wasn't the only one that suddenly found itself sitting on a lot of legacy code written in Python 2, a few months away from January 1st 2020. As you can imagine, the priority of migrating this code to Python 3 rose to high as some of the third party APIs we rely on started dropping Python 2 support, and the lucky engineer that got assigned this task was myself.

### Let 2to3 do the hard work

It's always good to let a script do the hard work, and Python comes bundled with a tool to help us with migration: [2to3](https://docs.python.org/3.7/library/2to3.html). The way it works is by matching patterns defined in 'fixers' with the code in your python files, and performing any necessary replacements (which are also defined in the fixers).

In Windows, I was able to find the script in the `Tools/scripts/` directory of the Python root and in Ubuntu I managed to install it running `apt-get install 2to3`. You can then run it like (`2to3` also supports directories instead of single files):
```
2to3 -w test2to3.py
```
If you wish to only see the diffs and not save any of the changes, skip the `-w` argument:
```
2to3 test2to3.py
```
This can be pretty useful during testing.

Also useful is creating your own [`my2to3.py`](https://stackoverflow.com/questions/24508357/how-to-launch-own-2to3-fixer) file:
```
import sys
from lib2to3.main import main

sys.path.append('path/to/my_own_package')
sys.exit(main('my_own_package.contained_fixers'))
```
And running your own custom fixers:
```
python my2to3.py -f my_fixer -w project
```

Most if not all the changes you need for your code to be Python 3 compatible will be handled by `2to3`, but when reviewing I found situations in which changes should have been made as well as situations where unnecessary changes were made. Let's go over those cases next.

### Using exceptions out of scope

At some point I ran into a retry logic implemented as a `for` loop that looked something like this:
```
for _ in range(2):
	try:
		raise ValueError('Hey!') # Example only
	except ValueError as e:
		print('Attempt {} of 2.'.format(_))
		continue
print('Failed too many times!')
raise e
```
One of the issues with this code is that in Python 3 `Exception` will not be bound outside of the `except` block and a `NameError` will be raised, where as in Python 2 this runs just fine. In case you're curious, this issue is explained in detail by [PEP 3110](https://www.python.org/dev/peps/pep-3110/#semantic-changes).

This case will not be caught by `2to3`, even though it includes a `fix_except.py` fixer. So it will be up to us to spot it manually and fix it:
```
for _ in range(2):
	try:
		function_that_raises_exception()
	except Exception as e:
		saved_exception = e
		print('Attempt {} of 2.'.format(_))
		continue
raise saved_exception # Failed too many times
```

### If working with `int` types, Python 2's division should be Python 3's floor division

Although it might seem a really obvious fix, it ended up slipping by an initial review as the division arguments weren't clearly integers and there wasn't any type hinting or test coverage, part of the fun of working with legacy code. It certainly didn't help that missing this change caused an exception to be raised somewhere else with a message completely unrelated to the underlying issue.

Decided I would not be the running in circles again to identify this issue, so I came up with the following fixer that can be added to a `2to3` run:

```
from lib2to3 import fixer_base
from lib2to3.fixer_util import Name

class FixDivision(fixer_base.BaseFix):

	BM_compatible = True
	PATTERN = "'/'"

	def transform(self, node, results):
		return Name("//", prefix=node.prefix)
```
I recommend running this fixer without saving changes at least once as the pattern will match any occurrence of the `/` operator, even when using floats, and could produce incorrect changes. In case you're wondering, it will not match strings that contain `'/'`.

### Do you really need a list?

There's a few methods and functions in Python 2 that return lists, whereas in Python 3 they return iterators: `dict` methods like `dict.keys`, `xrange`, `filter`, `zip`, and `map`. When you run `2to3`, there are fixers defined for each of these cases that wrap them in a `list` call or implements them as `list` comprehensions. For example:

```
d = {'a': 0, 'b': 1}
for _ in d.keys():
	print(_)

for _ in filter(lambda x: x > 0, d.keys()):
	print(_)

for _ in map(lambda x: x + 1, d.keys()):
	print(_)
```
Becomes:
```
d = {'a': 0, 'b': 1}
for _ in list(d.keys()):
	print(_)

for _ in [x for x in list(d.keys()) if x > 0]:
	print(_)

for _ in [x + 1 for x in list(d.keys())]:
	print(_)
```

As it's the case with this snippet, our legacy code didn't really need to use lists, so why not save ourselves the memory overhead and use the now default iterators instead? It should be pretty safe to exclude the `map` and `filter`fixes, as they only wrap the usage in a `list`:
```
2to3 test2to3.py -x filter -x map
```
However the `dict` fix does more than just wrap calls in `list`: it will also convert the method names to Python 3, which means you'll have to review each case. You can view specific diffs by running:
```
2to3 test2to3.py -f dict
```
I haven't mentioned `xrange` and `zip` as they actually skip the `list` wrap if the call is inside a `for` loop.

Keep in mind that this section is particularly dependent on your actual code, which is why I suggest looking at diffs first before committing any changes. In my case iterators did the trick just fine, but if you need a `list`, use it!

### Even if your code is Python 2 and 3 compatible, other people's might not

We take advantage of several third party libraries in our code base, many of which implemented Python 3 support only in newer versions. What this means is that you'll have to take a look at your project's `requirements.txt` file and make sure any fixed package versions are updated to support Python 3.

This section is more of a reminder as I could not think of any trick to speed up the process. In some cases you can ease the transition by specifying conditions to install libraries in pre-migration work. For example, our Python 2 code required `enum34`, however `enum` is part of the standard library from Python 3.4 onwards. Since we had anticipated a migration, we had a conditional defined: `enum34;python_version<3.4` which means no update to `requirements.txt` had to be done for this particular package during the migration.

### Final thoughts

I haven't talked about how crucial it is to have a strong test suite when doing refactoring. The reason I haven't is that in my particular case test coverage was weak if present at all, as it unfortunately can be the case with legacy code.

As a final recommendation, check out the [official porting guide](https://docs.python.org/3/howto/pyporting.html) which describes all the necessary changes to make your code compatible with Python 2 and Python 3.
