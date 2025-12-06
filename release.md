### Release Steps

```shell
# Add changes to CHANGELOG.md
# Update requirements.txt
# Change version in pyproject.toml
git add -u
git commit -m "Version X"
# Ensure CI passes before creating tag
git tag vX
git push origin main
git push origin vX
rm -r build dist htmlcov htmd.egg-info venv
find . -type d -name "__pycache__" -exec rm -r {} +
python3 -m venv venv
venv/bin/python -m pip install pip setuptools --upgrade
venv/bin/python -m pip install build --upgrade
venv/bin/python -m build
venv/bin/python -m pip install twine
venv/bin/twine check dist/*
venv/bin/twine upload dist/*
# Create new release in GitHub
# Upload wheel and archive from dist/
```
