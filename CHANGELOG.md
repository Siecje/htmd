# Change log

## [] - 
### Added
- `htmd preview` will re-create combined.min.css and combined.min.js for new files

## [5.1.0] - 2024-02-09
### Added
- `pip install htmd[dev]` to install development dependencies
- Support Python 3.13 and 3.14
- `htmd preview` will reload when posts are modified
### Fixed
- Fix `htmd preview` when static directory is not the default

## [5.0.0] - 2024-02-09
### Added
- `python -m htmd` will now work
- `styles` block in `_layout.html` template
- `scripts` block in `_layout.html` template
- draft: build to add draft to build
- `preview --drafts` to view site as if all drafts are published
### Changed
- Ignore Frozen-Flask MissingURLGeneratorWarning
- `htmd preview` will reload when static files change
- Drafts will be served with /draft/ URL prefix
### Fixed
- `htmd preview` will only serve pages
- `htmd preview` will show 404 for authors that don't exist
- build draft without published
- errors when a config folder did not exist

## [4.0.0] - 2024-01-27
### Added
- Set post time on build
- Add published or updated on build
- Draft posts
- Build all pages instead of just pages that are linked to from the site
### Changed
- `tags` sent to all_tags.html is now a dict
- Hide Python warnings when using `htmd`
### Fixed
- Atom feed URL
- Using wheel without installing

## [3.0.0] - 2023-12-08
### Added
- Use toml for the config file
- `htmd` will work from child directories in the project
### Removed
- Dropped support for Python 3.10

## [2.0.3] - 2023-12-08
### Added
- `--version` option

## [2.0.2] - 2023-12-08
### Added
- Use only pyproject.toml
### Removed
- `__init__.py` files in example_site

## [2.0.1] - 2023-12-07
### Added
- Python 3.12 support
### Fixed
- Remove deprecation warnings

## [2.0.0] - 2022-03-19
### Added
- Python 3 support
- --all-templates option for `htmd start`
- templates command
- 404 page
- tests

## [1.5.0] - 2015-02-16
### Added
- setting MINIFY_HTML to minify resulting HTML
- setting PRETTY_HTML to fix indentation of resulting HTML
### Fixed
- SITE_NAME bug in og:site_name

## [1.4.0] - 2015-02-15
### Added
- tag class to tag links
- option to prevent minification of JS, CSS, and HTML
- pygments stylesheet
- default styles for Markdown elements

## [1.3.0] - 2015-02-15
### Added
- option to show the beginning of the post in lists.
### Removed
- default links styles for posts in lists.

## [1.2.1] - 2015-02-12
### Added
- option to show the beginning of the post in lists.

### Removed
- default links styles for posts in lists.

## [1.2.0] - 2015-02-12
### Changed
- getting install_requires from requirements.txt

## [1.1.0] - 2015-02-01
### Changed
- `.js` files in the static directory are combined and minified and combined.min.js is used in `_layout.html`
- `.css` files in the static directory are combined and minified and combined.`min.css` is used in `_layout.html`

## [1.0.0] - 2015-01-31
### Added
- posts are sorted
- routes for tags and authors
- tags are sized based on number of times used
- custom meta tags and use in templates
- override templates
- separate folders for posts (think blog) and pages (think about, contact)
- Atom feed for all posts
- multiple author support
