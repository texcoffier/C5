
PYTOJS = nodejs RapydScript/bin/rapydscript --prettify --bare

%.js:%.py compatibility.py options.py compile.py question.py compile_[!s]*.py
	@echo '$*.py → $*.js'
	@case $* in \
	COMPILE*) \
		COMPILER=$$(echo $* | sed -e 's,/.*,,' | tr '[A-Z]' '[a-z]') ; \
		FILES="compatibility.py options.py compile.py question.py $$COMPILER.py $*.py" ; \
		SESSION=$$(echo ; echo 'if not Compile.worker: Session([' ; \
		grep '^class.*(Question)' $*.py | sed -r 's/.*class *(.*)\(Question\).*/\1(),/' ;\
		echo '])') ; \
		Q=1 ; \
		[ -d $* ] && chmod 700 $* ; \
		;; \
	*) \
		FILES="compatibility.py options.py $*.py" ;\
		Q=0 \
		;; \
	esac ; \
	cat $$FILES > $*.py.xxx ; \
	echo "$$SESSION" >> $*.py.xxx ; \
	$(PYTOJS) $*.py.xxx >$*.js && \
	([ $$Q = 1 ] && (cat options.py compile.py $$COMPILER.py question_before.py $*.py question_after.py | tee xxx.py | python3 >$*.json) || true) && \
	rm $*.py.xxx

default:all
	@./utilities.py open # Open page on browser

sandbox:
	git clone "https://github.com/cloudflare/sandbox.git"
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

prepare:RapydScript node_modules/brython HIGHLIGHT xxx-JSCPP.js node_modules/alasql sandbox killer \
	ccccc.js adm_root.js adm_course.js adm_session.js checkpoint.js home.js \
	favicon.ico node_modules/@jcubic/lips
	@$(MAKE) $$(echo COMPILE_*/*.py | sed 's/\.py/.js/g')
	@if [ ! -d SSL ] ; then ./utilities.py SSL-SS ; fi

all:prepare
	@echo
	@./utilities.py start

############# Utilities ############
RapydScript:
	git clone https://github.com/atsepkov/RapydScript.git

HIGHLIGHT:
	@mkdir $@
	cd $@ && HERE=$$(pwd) && \
	cd /tmp && \
	git clone https://github.com/highlightjs/highlight.js.git && \
	cd highlight.js && \
	npm install commander && \
	node tools/build.js -t browser :common :lisp && \
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
	rm xxx*
kill:
	-pkill -f http_server.py
	-pkill -f compile_server.py
pre-commit:
	@echo "Running regression tests before commiting (it takes 2 minutes)"
	./tests.py hidden 1 2>&1 | tee xxx.regtests | grep -e FIREFOX -e CHROME
	@echo "It is fine!"
	@rm xxx.regtests

# Update document from sources

options.html:options.py utilities.py
	./utilities.py options.html >options.html

DOCUMENTATION/index.html:options.html Makefile
	awk '/START_OPTIONS/ { D=1; print $$0; next; } \
	     D==1 && /<\/div END>/ { system("cat options.html"); D=0; } \
		 D==0 { print($$0); }' <DOCUMENTATION/index.html >xxx.new
	mv xxx.new $@
