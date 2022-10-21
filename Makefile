
PYTOJS = nodejs RapydScript/bin/rapydscript --prettify --bare

%.js:%.py compatibility.py compile.py question.py compile_[!s]*.py
	@echo '$*.py → $*.js'
	@case $* in \
	COMPILE*) \
		COMPILER=$$(echo $* | sed -e 's,/.*,,' | tr '[A-Z]' '[a-z]') ; \
		FILES="compatibility.py compile.py question.py $$COMPILER.py $*.py" ; \
		SESSION=$$(echo ; echo 'if not Compile.worker: Session([' ; \
		grep '^class.*(Question)' $*.py | sed -r 's/.*class *(.*)\(Question\).*/\1(),/' ;\
		echo '])') \
		;; \
	*) \
		FILES="compatibility.py $*.py" \
		;; \
	esac ; \
	cat $$FILES > $*.py.xxx ; \
	echo "$$SESSION" >> $*.py.xxx ; \
	$(PYTOJS) $*.py.xxx >$*.js && \
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

favicon.ico:c5.svg
	inkscape --export-area-drawing --export-png=$@ $?

prepare:RapydScript node_modules/brython HIGHLIGHT xxx-JSCPP.js node_modules/alasql sandbox \
	ccccc.js adm_root.js adm_home.js adm_course.js checkpoint.js favicon.ico
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
	node tools/build.js -t browser :common && \
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

############# Misc ############
lint:
	pylint [^x]*.py
clean:
	rm xxx*
kill:
	-pkill -f http_server.py
	-pkill -f compile_server.py
