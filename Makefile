%.js:%.py
	nodejs $(HOME)/TOMUSS/TOMUSS/PYTHON_JS/RapydScript/bin/rapydscript \
		--prettify --bare $*.py >$*.js

all:xxx-highlight.js xxx-JSCPP.js node_modules/brython xxx-ccccc.js xxx-worker.js xxx-worker-cpp.js xxx-worker-python.js

xxx-highlight.js:
	HERE=$$(pwd) && \
	cd /tmp && \
	git clone https://github.com/highlightjs/highlight.js.git && \
	cd highlight.js && \
	npm install commander && \
	node tools/build.js -t browser :common && \
	cp build/highlight.min.js $$HERE/xxx-highlight.js && \
	cp build/demo/styles/default.css $$HERE/xxx-highlight.css

xxx-JSCPP.js:
	GET https://raw.githubusercontent.com/felixhao28/JSCPP/gh-pages/dist/JSCPP.es5.min.js >$@

node_modules/brython:
	npm install brython

xxx-ccccc.py:ccccc.py Makefile
	cat compatibility.py ccccc.py >$@
xxx-worker.py:compile.py compile_js.py question.py course.py Makefile
	cat compatibility.py compile.py compile_js.py question.py course.py >$@
xxx-worker-cpp.py:compile.py compile_cpp.py question.py course_cpp.py Makefile
	cat compatibility.py compile.py compile_cpp.py question.py course_cpp.py >$@
xxx-worker-python.py:compile.py compile_python.py question.py course_python.py Makefile
	cat compatibility.py compile.py compile_python.py question.py course_python.py >$@

lint:
	pylint [^x]*.py

install:all
	cp --update ccccc.html xxx-*.js $(HOME)/public_html/CCCCC

# regtest:xxx-regtest-py xxx-regtest-js
# 	if diff -u xxx-regtest-py xxx-regtest-js ; \
# 	then cat xxx-regtest-py ; echo ; echo "Regtests are fine" ; echo ; fi
# xxx-regtest-js:xxx-ccccc.js
# 	node xxx-ccccc.js >$@
# xxx-regtest-py:xxx-merged.py
# 	python3 xxx-merged.py >$@

clean:
	rm xxx*
