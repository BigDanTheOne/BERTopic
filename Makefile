test:
	pytest

install:
	python -m pip install -e .

install-gpu:
	python -m pip install -e .
	conda create -n rapids-21.12 -c rapidsai -c nvidia -c conda-forge rapids=21.12 python=3.7 cudatoolkit=11.2 dask-sql

install-test:
	python -m pip install -e ".[test]"
	python -m pip install -e ".[all]"

pypi:
	python setup.py sdist
	python setup.py bdist_wheel --universal
	twine upload dist/*

clean:
	rm -rf **/.ipynb_checkpoints **/.pytest_cache **/__pycache__ **/**/__pycache__ .ipynb_checkpoints .pytest_cache

check: test clean
