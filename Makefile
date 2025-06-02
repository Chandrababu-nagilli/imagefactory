sdist:
	python3 setup.py sdist

signed-rpm: sdist
	rpmbuild -ba imagefactory.spec --define "_sourcedir `pwd`/dist" --define "__python /usr/bin/python3"

rpm: sdist
	rpmbuild -ba imagefactory.spec --define "_sourcedir `pwd`/dist" --define "__python /usr/bin/python3"

srpm: sdist
	rpmbuild -bs imagefactory.spec --define "_sourcedir `pwd`/dist" --define "__python /usr/bin/python3"

pylint:
	@python3 -m pylint --rcfile=pylint.conf imagefactory imgfac

unittests:
	PYTHONPATH=. python3 -m unittest tests.testReservationManager

clean:
	rm -rf MANIFEST build dist imagefactory.spec
