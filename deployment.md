### Deployment

```shell
git clone git@github.com:Siecje/htmd.git
cd htmd
python3 -m venv venv
venv/bin/python -m pip install pip setuptools wheel --upgrade
venv/bin/python -m pip install build --upgrade
venv/bin/python -m build
venv/bin/python -m pip install twine
venv/bin/twine check dist/*
venv/bin/twine upload dist/*
```
