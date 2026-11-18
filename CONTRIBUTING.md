# How to contribute

With the many games the B3 project supports, third party patches are essential to keep the project great. There are a
few guidelines that we need contributors to follow so that we can have a chance of keeping B3 project as clean and
organized as possible.

****************

## Development setup (Python 3.11+)

```bash
python -m venv .venv
.venv/bin/pip install -e ".[postgresql,test]"
```

Run the test suite (xdist, whole suite ≈ 40 s):

```bash
.venv/bin/pytest
.venv/bin/pytest tests/core -q                     # core only
.venv/bin/pytest tests/plugins/admin -q            # one plugin
.venv/bin/pytest tests/core/test_config.py -q -k getpath   # single test
```

Lint:

```bash
.venv/bin/ruff check b3 tests
```

Storage tests for MySQL/PostgreSQL require running servers and `MYSQL_TEST_*` /
`POSTGRESQL_TEST_*` environment variables; they skip cleanly otherwise (CI
provides `mysql:8` and `postgres:16` service containers).

## Contributing Issues

Issues submitted on Github must be technically documented with the aim that any contributor trying to fix your issue
should have enough information to understand and reproduce the issue and validate the fix.

* Make sure you have a [GitHub account](https://github.com/signup/free).
* Search for a similar issue.
* Submit your issue, assuming one does not already exist.
* Clearly describe the issue including:
    * Steps to reproduce.
    * Expected results.
    * Actual results.

## Contributing Code

We prefer contributors to submit their code change throught GitHub [pull requests](http://help.github.com/send-pull-requests/).

* [Fork](https://github.com/BigBrotherBot/big-brother-bot/fork) this repository on GitHub.
* Create a topic branch from where you want to base your work. Please avoid working directly on the `master` branch.
* Make sure your code follows our [coding style](#coding-style).
* Make commits of logical units.
* Use [Conventional Commits](https://www.conventionalcommits.org/) for messages: lowercase, imperative subject
  (`fix(parsers): ...`, `feat(plugins): ...`, `test: ...`), optional body explaining the why.
* Make sure you have added all the necessary tests for your changes.
* Make sure that all the provided tests pass before sending a pull request.
* Squash multiple trivial commits into a single commit.

# Submitting Your Changes

* Push your changes to a topic branch in your fork of the repository.
* Submit a pull request to the BigBrotherBot/big-brother-bot repository.
* A pull request should contain a single feature/bugfix. If you need to send multiple features/bugfixes please
  use separate pull requests.

## Coding Style

Different programmers use to write code in different ways. Without the usage of coding conventions, a project source code
may become unreadable and eventually not understandable. While B3 doesn't strictly follows PEP-8 coding conventions, it
is required that your code follows the following guidelines:

* Break long lines after 120 characters (matches `ruff` line-length in `pyproject.toml`).
* Do not indent using `TAB`: use 4 spaces to indent your code.
* Do not use python built-in names to name your variables.
* Document your code (example below):
```python
def myFunc(self, param1, param2):
   """
   Put the description here.
   :param param1: The first parameter.
   :param param2: The second parameter.
   :raise MyError: The exception class if your function may raise an exception.
   :return: The return value of your function.
   """
   ...
```
* Always use `self` for the first argument to instance methods.
* Always use `cls` for the first argument to class methods.
* Use uppercase for SQL keywords and lowercase for SQL identifiers.
* When catching exceptions, mention specific exceptions whenever possible instead of using only the `except` keyword.
* When you add new python modules remember to place the licensing on the top of the file.
* Remember to update the changelog whenever you make user visible changes.
* Last but not least: comment your code!

****************

# Additional Resources

* [Bug tracker](https://github.com/BigBrotherBot/big-brother-bot/issues)
* [General GitHub documentation](http://help.github.com/)
* [GitHub pull request documentation](http://help.github.com/send-pull-requests/)
