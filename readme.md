# htmd

htmd allows you to write Markdown and use templates to create a static website.
Yes it is another static site generator.

## Why another static site generator?

I admit I didn't try them [all](https://staticsitegenerators.net/).
I tried several static site generators written in Python, but I found them complicated.
Some static site generators I tried created a template website with content on the home page but the index.html file had no content.
I think it should be obvious where the content is coming from.

- I didn't like starting with a lot of folders and files
- I want all blog posts in the same folder because it is easier to work with.
I want the URL structure for each post to include the date (/2015/01/31/post-title), without having to create a folder for each year and month.
- I didn't want to include all of the templates being used, only overwrite the ones I modified.
- I wanted it to be obvious where the content was coming from.
- I want it be obvious how to set a value to use in multiple templates.
- If you made changes to one of your templates and ran build you wouldn't update existing files unless you deleted your build folder everytime.

I believe the reason there are so many static site generators is people are picky about their workflow and that's okay.
This is also a learning experience creating a Python package with a cli.

## What is the difference between posts and pages?

Posts are blog posts with dates and authors tracked by feeds.
Pages are other webpages on the site, for example the About page.

## How do I edit the layout of the site?

Edit the `templates/_layout.html` file that was created when running `htmd start`.
This a [Jinja 2](http://jinja.pocoo.org/docs/dev/templates/#template-inheritance) template that all other pages will use by default.
You can add a link to CSS file that you have created in `static/`.
To change other pages you will need to override the page template by creating a file with the same name in the `templates/` folder.
The complete list of templates can be found [here](https://github.com/Siecje/htmd/tree/main/htmd/templates).

## Getting Started

```shell
$ pip install htmd
```

```shell
Commands:
  start      Create example files to get started.
  verify     Verify posts formatting is correct.
  build      Create static version of the site.
  preview    Serve files to preview site.
  templates  Create any missing templates
```
