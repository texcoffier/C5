PYS = ccccc.py

xxx-ccccc.js:xxx-merged.py Makefile
	nodejs $(HOME)/TOMUSS/TOMUSS/PYTHON_JS/RapydScript/bin/rapydscript \
		--prettify --bare xxx-merged.py >$@

xxx-merged.py:$(PYS)
	cat $(PYS) >$@

lint:$(PYS)
	pylint $(PYS)

install:xxx-ccccc.js
	cp --update ccccc.html xxx-ccccc.js $(HOME)/public_html/CCCCC

# regtest:xxx-regtest-py xxx-regtest-js
# 	if diff -u xxx-regtest-py xxx-regtest-js ; \
# 	then cat xxx-regtest-py ; echo ; echo "Regtests are fine" ; echo ; fi
# xxx-regtest-js:xxx-ccccc.js
# 	node xxx-ccccc.js >$@
# xxx-regtest-py:xxx-merged.py
# 	python3 xxx-merged.py >$@

clean:
	rm xxx*
