# htmd

htmd allows you to write Markdown and use templates to create a static website.
Yes it is another static site generator.

## Getting Started

```shell
pip install htmd
```

`htmd --help`
```shell
Usage: htmd [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  build      Create static version of the site.
  preview    Serve files to preview site.
  start      Create example files to get started.
  templates  Create any missing templates.
  verify     Verify posts formatting is correct.
```

## Why another static site generator?

I admit I didn't try them [all](https://staticsitegenerators.net/).
I tried several static site generators written in Python, but I found them complicated.
Some static site generators I tried created a template website with content on the home page but the index.html file had no content.
It should be obvious where to find the content.

- I don't like starting with a lot of folders and files
- I want all blog posts in the same folder because it is easier to work with.
I want the URL structure for each post to include the date (/2015/01/31/post-title), without having to create a folder for each year and month.
- I don't want to include all of the templates being used, only overwrite the ones I modified.
- I want it to be obvious where to find the content.
- I want it to be obvious how to set a value to use in multiple templates.
- If you made changes to one of your templates and ran build you wouldn't update existing files unless you deleted your build folder everytime.

I believe the reason there are so many static site generators is people are picky about their workflow and that's okay.
This is also a great way to stay up to date with packaging in Python.

## What is the difference between posts and pages?

Posts are blog posts with dates and authors tracked by feeds.
Pages are other webpages on the site, for example the About page.

## How do I edit the layout of the site?

Edit the `templates/_layout.html` file that was created when running `htmd start`.
This a [Jinja](https://jinja.palletsprojects.com/en/stable/templates/#template-inheritance) template that all other pages will use by default.
You can add a link to CSS files that you have created in `static/`.
To change other pages you will need to override the page template by creating a file with the same name in the `templates/` folder.
The complete list of templates can be found [here](https://github.com/Siecje/htmd/tree/main/htmd/example_site/templates).

## How do drafts work?

A post will be a draft if `draft: true` is set in the metadata and will not appear in the build folder.
If `draft: build` is set then the post page will be in the build but the post will not appear in any list pages. When a draft is built the metadata value will contain a UUID of where the post is available.

For example, if the draft metadata is `draft: build|f47d4d98-9d66-448a-9e08-7b5c2032e558` then the post will served at `/draft/f47d4d98-9d66-448a-9e08-7b5c2032e558/index.html`.

To view the site as if all drafts were published run `htmd preview --drafts`. 

## How do I password protect a post?

A post will be password protected if `password:` exists in the post metadata.

On `htmd build` a password will be added as the value of the `password` metadata field.

If publishing to a public repo the page contents and password should not be visible.
Password protected posts can go into the `posts/password-protect/` directory
which can be ignored by source control.

When you open a password protect post in the browser there will be a password prompt
if the correct password is entered you can read the post.

## Since there is no backend server how are the contents hidden?

The page contents are encrypted in the JavaScript of the HTML document.
Only if the correct private key is provided will the contents be shown.

## Development

### Running the development version locally

```shell
git clone https://github.com/Siecje/htmd.git
python3 -m venv venv
venv/bin/python -m pip install pip setuptools --upgrade
venv/bin/python -m pip install -e "htmd/[dev]"
# You can now make changes inside htmd/ without having to re-install
mkdir my_site
cd my_site
../venv/bin/htmd start
# You can also create a symlink to htmd
# somewhere on your $PATH and just use `htmd start`
../venv/bin/htmd build
```

### Running mypy

```shell
venv/bin/python -m mypy .
```

### Running ruff

```shell
venv/bin/python -m ruff check
```

### Running the tests

```shell
git clone https://github.com/Siecje/htmd.git
cd htmd
python3 -m venv venv
venv/bin/python -m pip install pip setuptools --upgrade
venv/bin/python -m pip install -e .[dev]
venv/bin/python -m pytest .
```

#### Running the tests with coverage.py

```shell
venv/bin/coverage run -m pytest .
venv/bin/coverage html
open htmlcov/index.html
```
