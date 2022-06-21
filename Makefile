
PYTOJS = nodejs RapydScript/bin/rapydscript --prettify --bare

%.js:%.py
	@echo '$*.py → $*.js'
	@case $* in \
	course_*) \
		COMPILER=$$(echo $* | sed -r -e 's/course_([^_]*).*/\1/') ; \
		FILES="compatibility.py compile.py question.py compile_$$COMPILER.py $*.py" \
		;; \
	*) \
		FILES="compatibility.py $*.py" \
		;; \
	esac ; \
	cat $$FILES > xxx-$*.py ; \
	$(PYTOJS) xxx-$*.py >$*.js ; \
	rm xxx-$*.py

default:all
	@xdg-open http:127.0.0.1:8000/index.html

all:RapydScript node_modules/brython xxx-highlight.js xxx-JSCPP.js ccccc.js
	@$(MAKE) $$(echo course*.py | sed 's/\.py/.js/g')
	@echo
	@echo "All seems fine."
	@echo "You can now copy the result on a web page:"
	@echo
	@echo "cp --recursive --update ccccc.html index.html xxx*.css *.js brython/ $(HOME)/public_html/CCCCC"
	@echo
	@echo "Launching web server"
	@-./http_server.py &
	@echo "Launching compilation server (only needed for compile_remote.py)"
	@-./compile_server.py &

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
	-rm brython
	npm install brython@3.10.6
	ln -s node_modules/brython .
xxx-JSCPP.js:
	GET https://raw.githubusercontent.com/felixhao28/JSCPP/gh-pages/dist/JSCPP.es5.min.js >$@


############# Dependencies ############

FRAMEWORK=ccccc.py compile.py question.py
course_python.js:$(FRAMEWORK) compile_python.py course_python.py
course_js.js:$(FRAMEWORK) compile_js.py course_js.py
course_cpp.js:$(FRAMEWORK) compile_cpp.py course_cpp.py
course_remote.js:$(FRAMEWORK) compile_remote.py course_remote.py



lint:
	pylint [^x]*.py
clean:
	rm xxx*
kill:
	-pkill -f http_server.py
	-pkill -f compile_server.py
