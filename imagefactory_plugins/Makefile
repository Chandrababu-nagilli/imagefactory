sdist:
	python3 setup.py sdist

signed-rpm: sdist
	rpmbuild -ba imagefactory-plugins.spec --define "_sourcedir `pwd`/dist" --define "__python /usr/bin/python3"

rpm: sdist
	rpmbuild -ba imagefactory-plugins.spec --define "build_mock 1" --define "_sourcedir `pwd`/dist" --define "__python /usr/bin/python3"

rpmnomock: sdist
	rpmbuild -ba imagefactory-plugins.spec --define "_sourcedir `pwd`/dist" --define "__python /usr/bin/python3"

srpm: sdist
	rpmbuild -bs imagefactory-plugins.spec --define "_sourcedir `pwd`/dist" --define "__python /usr/bin/python3"

pylint:
	python3 -m pylint --rcfile=.pylintrc imagefactory imgfac

unittests:
	python3 -m unittest discover -v

clean:
	rm -rf MANIFEST build dist imagefactory-plugins.spec
