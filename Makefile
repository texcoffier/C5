PYS = compatibility.py ccccc.py compile.py compile_js.py question.py course.py

%.js:%.py
	nodejs $(HOME)/TOMUSS/TOMUSS/PYTHON_JS/RapydScript/bin/rapydscript \
		--prettify --bare $*.py >$*.js

all:xxx-ccccc.js xxx-worker.js

xxx-ccccc.py:ccccc.py Makefile
	cat compatibility.py ccccc.py >$@
xxx-worker.py:compile.py compile_js.py question.py course.py Makefile
	cat compatibility.py compile.py compile_js.py question.py course.py >$@

lint:$(PYS)
	pylint $(PYS)

install:all
	cp -r --update ccccc.html xxx-ccccc.js xxx-worker.js HIGHLIGHT $(HOME)/public_html/CCCCC

# regtest:xxx-regtest-py xxx-regtest-js
# 	if diff -u xxx-regtest-py xxx-regtest-js ; \
# 	then cat xxx-regtest-py ; echo ; echo "Regtests are fine" ; echo ; fi
# xxx-regtest-js:xxx-ccccc.js
# 	node xxx-ccccc.js >$@
# xxx-regtest-py:xxx-merged.py
# 	python3 xxx-merged.py >$@

clean:
	rm xxx*
