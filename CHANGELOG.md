# Change log

## [4.0.0] - 2024-
### Added
- Set post time on build
- Add published or updated on build
### Changed
- tags sent to all_tags.html is now a dict
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
