%.js:%.py
	nodejs RapydScript/bin/rapydscript --prettify --bare $*.py >$*.js

all:RapydScript node_modules/brython \
    xxx-highlight.js xxx-JSCPP.js xxx-ccccc.js \
	xxx-worker.js xxx-worker-cpp.js xxx-worker-python.js
	@echo
	@echo "And now copy the result on a web page:"
	@echo
	@echo "cp --recursive --update ccccc.html xxx-*.js brython/ $(HOME)/public_html/CCCCC"

############# Utilities ############
RapydScript:
	git clone https://github.com/atsepkov/RapydScript.git

xxx-highlight.js:
	HERE=$$(pwd) && \
	cd /tmp && \
	git clone https://github.com/highlightjs/highlight.js.git && \
	cd highlight.js && \
	npm install commander && \
	node tools/build.js -t browser :common && \
	cp build/highlight.min.js $$HERE/xxx-highlight.js && \
	cp build/demo/styles/default.css $$HERE/xxx-highlight.css

############# Compilers ############
node_modules/brython:
	npm install brython
	ln -s node_modules/brython .
xxx-JSCPP.js:
	GET https://raw.githubusercontent.com/felixhao28/JSCPP/gh-pages/dist/JSCPP.es5.min.js >$@

############# GUI ############
xxx-ccccc.py:ccccc.py
	cat compatibility.py ccccc.py >$@

############# Courses ############
CORE = compatibility.py compile.py question.py

xxx-worker.py:$(CORE) compile_js.py course.py
	cat $^ >$@
xxx-worker-cpp.py:$(CORE) compile_cpp.py course_cpp.py
	cat $^ >$@
xxx-worker-python.py:$(CORE) compile_python.py course_python.py
	cat $^ >$@

lint:
	pylint [^x]*.py

clean:
	rm xxx*
