
JS/%.js: JS %.py compatibility.py options.py compile.py question.py compile_[!s]*.py xxx_local.py
	@./py2js $* || true
%.js: %.py compatibility.py options.py compile.py question.py compile_[!s]*.py xxx_local.py
	@./py2js $* || true

xxx_local.py:common.py coach.py $(C5_CUSTOMIZE)
	cat common.py coach.py $(C5_CUSTOMIZE) >$@

$(C5_CUSTOMIZE):
	echo '"""Redefine «common.py» functions here (as in «local_ucbl.py»)"""' >$@

default:all
	@./c5.py open # Open page on browser

JS:
	mkdir JS

sandbox/libsandbox.so:
	-[ ! -d sandbox ] && git clone "https://github.com/cloudflare/sandbox.git"
	(cd sandbox ; \
	curl -L -O https://github.com/seccomp/libseccomp/releases/download/v2.4.3/libseccomp-2.4.3.tar.gz ; \
    tar xf libseccomp-2.4.3.tar.gz && mv libseccomp-2.4.3 libseccomp ; \
    (cd libseccomp && ./configure --enable-shared=no && make) ; \
	make libsandbox.so)

launcher:launcher.c
	$(CC) -Wall $@.c -o $@
	chown root $@
	chmod u+s $@

killer:killer.c

favicon.ico:c5.svg
	inkscape --export-area-drawing --export-png=$@ $?

prepare:RapydScript node_modules/brython HIGHLIGHT xxx-JSCPP.js node_modules/alasql sandbox/libsandbox.so killer \
	JS/ccccc.js JS/live_link.js JS/adm_root.js JS/adm_course.js JS/adm_session.js \
	JS/checkpoint.js JS/checkpoint_list.js JS/home.js JS/stats.js \
	favicon.ico node_modules/@jcubic/lips
	@$(MAKE) -j $$(nproc) $$(echo COMPILE_*/*/*.py | sed 's/\.py/.js/g')
	@if [ ! -d SSL ] ; then ./c5.py SSL-SS ; fi

all:prepare
	@echo
	@./c5.py start

############# Utilities ############
RapydScript:
	git clone https://github.com/atsepkov/RapydScript.git

HIGHLIGHT:
	@mkdir $@
	cd $@ && HERE=$$(pwd) && \
	cd /tmp && \
	(git clone https://github.com/highlightjs/highlight.js.git || true) && \
	cd highlight.js && \
	npm install commander && \
	node tools/build.js -t browser :common lisp coq && \
	cp build/highlight.min.js $$HERE/highlight.js && \
	cp -r src/styles/* $$HERE
	rm -rf /tmp/highlight.js

############# Compilers ############
node_modules/brython:
	npm install brython@3.10.5 # 3.10.6 not working (missing module_id)
xxx-JSCPP.js:
	GET https://raw.githubusercontent.com/felixhao28/JSCPP/gh-pages/dist/JSCPP.es5.min.js >$@
node_modules/alasql:
	npm install alasql@1.7.2
node_modules/@jcubic/lips:
	npm install @jcubic/lips
	sed -i 's/(token.token || token)/(token.toUpperCase ? token : token.token)/' \
	    "node_modules/@jcubic/lips/src/lips.js"
############# Misc ############
lint:
	-mypy dns_server.py infos_server.py http_server.py compile_server.py
	pylint [^x]*.py
clean:
	-rm -r xxx* COMPILE_REMOTE/test/LOGS/anonyme_* COMPILE_REMOTE/test/session.cf \
	      *.log *.js *~ COMPILE_*/*~ COMPILE_*/questions.js COMPILE_*/questions.json \

kill:
	-pkill -f http_server.py
	-pkill -f compile_server.py
pre-commit:
	@echo "Running regression tests before commiting (it takes 2 minutes)"
	unset MAKEFLAGS MAKELEVEL ; \
	./tests.py CHROME hidden nosleep 1 2>&1 | tee xxx.regtests | grep -e FIREFOX -e CHROME
	@if grep 'TESTS FAILED' xxx.regtests ; then cat xxx.regtests ; exit 1 ; fi
	@echo "It is fine!"
	@rm xxx.regtests

# Update document from sources

options.html:options.py c5.py utilities.py
	./c5.py options.html >options.html

DOCUMENTATION/index.html:options.html Makefile
	awk '/START_OPTIONS/ { D=1; print $$0; next; } \
	     D==1 && /<\/div END>/ { system("cat options.html"); D=0; } \
		 D==0 { print($$0); }' <DOCUMENTATION/index.html >xxx.new
	mv xxx.new $@
