
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
	@./utilities.py open # Open page on browser

sandbox:
	git clone "https://github.com/cloudflare/sandbox.git"
	(cd sandbox ; \
	curl -L -O https://github.com/seccomp/libseccomp/releases/download/v2.4.3/libseccomp-2.4.3.tar.gz ; \
    tar xf libseccomp-2.4.3.tar.gz && mv libseccomp-2.4.3 libseccomp ; \
    (cd libseccomp && ./configure --enable-shared=no && make) ; \
	make libsandbox.so)

prepare:RapydScript node_modules/brython xxx-highlight.js xxx-JSCPP.js ccccc.js adm_home.js sandbox course_js_done.js course_js_pending.js
	if [ ! -d TICKETS ] ; then mkdir TICKETS ; fi
	@$(MAKE) $$(echo course*.py | sed 's/\.py/.js/g')

all:prepare
	@echo
	@./utilities.py start

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
