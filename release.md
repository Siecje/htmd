### Release Steps

- Change version in pyproject.toml
- Add changes to CHANGELOG.md

```shell
git add -u
git commit -m "Version X"
git tag vX
git push origin main
git push origin vX
rm -r dist
rm -r venv
rm -r htmd.egg-info
find . -type d -name "__pycache__" -exec rm -r {} +
python3 -m venv venv
venv/bin/python -m pip install pip setuptools --upgrade
venv/bin/python -m pip install build --upgrade
venv/bin/python -m build
venv/bin/python -m pip install twine
venv/bin/twine check dist/*
venv/bin/twine upload dist/*
```


- Create new release in GitHub
