# Change log

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
- .js files in the static directory are combined and minified and combined.min.js is used in _layout.html
- .css files in the static directory are combined and minified and combined.min.css is used in _layout.html

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
