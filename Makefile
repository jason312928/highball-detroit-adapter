PYTHON ?= python3

.PHONY: check static test

check: static test

static:
	$(PYTHON) -c 'import ast, pathlib; [ast.parse(p.read_text(), filename=str(p)) for folder in ("scripts", "tests", "audio") for p in pathlib.Path(folder).glob("*.py")]'
	@for script in *.sh vendor/*.sh audio/*.sh; do bash -n "$$script" || exit; done
	@git diff --check

test:
	$(PYTHON) -B -m unittest discover -s tests -p 'test_*.py' -v
