
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

all:RapydScript node_modules/brython xxx-highlight.js xxx-JSCPP.js ccccc.js
	@$(MAKE) $$(echo course*.py | sed 's/\.py/.js/g')
	@echo
	@echo "And now copy the result on a web page:"
	@echo
	@echo "cp --recursive --update ccccc.html index.html xxx*.css *.js brython/ $(HOME)/public_html/CCCCC"

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



lint:
	pylint [^x]*.py
clean:
	rm xxx*
