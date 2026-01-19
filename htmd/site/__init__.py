from pathlib import Path
import sys
import tomllib
import typing

from flask import Flask
from jinja2 import ChoiceLoader, FileSystemLoader

from .freezer import freeze_bp, freezer
from .main import main_bp
from .pages import pages
from .posts import posts, posts_bp, reload_posts


def get_project_dir() -> Path:
    current_directory = Path.cwd()

    while not (current_directory / 'config.toml').is_file():
        parent_directory = current_directory.parent

        if current_directory == parent_directory:
            return Path.cwd()

        current_directory = parent_directory

    return current_directory


def create_app(*, show_drafts: bool = False) -> Flask:
    this_dir = Path(__file__).parent
    app = Flask(
        __name__,
        # default templates
        template_folder=this_dir / '..' / 'example_site' / 'templates',
    )
    app.register_blueprint(freeze_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(pages)
    app.register_blueprint(posts_bp)
    project_dir = get_project_dir()

    try:
        with (project_dir / 'config.toml').open('rb') as config_file:
            htmd_config = tomllib.load(config_file)
    except FileNotFoundError:
        msg = 'Can not find config.toml'
        sys.exit(msg)

    # Flask configs are flat, config.toml is not
    # Define the configuration keys and their default values
    # 'Flask config': [section, key, default]
    config_keys : dict[str, tuple[str, str, typing.Any]] = {
        'SITE_NAME': ('site', 'name', ''),
        'SITE_URL': ('site', 'url', ''),
        'SITE_LOGO': ('site', 'logo', ''),
        'SITE_DESCRIPTION': ('site', 'description', ''),
        'SITE_TWITTER': ('site', 'twitter', ''),
        'SITE_FACEBOOK': ('site', 'facebook', ''),
        'FACEBOOK_APP_ID': ('site', 'facebook_app_id', ''),

        'BUILD_FOLDER': ('folders', 'build', 'build'),
        'PAGES_FOLDER': ('folders', 'pages', 'pages'),
        'POSTS_FOLDER': ('folders', 'posts', 'posts'),
        'STATIC_FOLDER': ('folders', 'static', 'static'),
        'TEMPLATE_FOLDER': ('folders', 'templates', 'templates'),

        'POSTS_EXTENSION': ('posts', 'extension', '.md'),

        'PRETTY_HTML': ('html', 'pretty', False),
        'MINIFY_HTML': ('html', 'minify', False),

        'SHOW_AUTHOR': ('author', 'show', True),
        'DEFAULT_AUTHOR': ('author', 'default_name', ''),
        'DEFAULT_AUTHOR_TWITTER': ('author', 'default_twitter', ''),
        'DEFAULT_AUTHOR_FACEBOOK': ('author', 'default_facebook', ''),
    }
    # Update app.config using the configuration keys
    for flask_key, (table, key, default) in config_keys.items():
        app.config[flask_key] = htmd_config.get(table, {}).get(key, default)
    app.config['SERVER_NAME'] = app.config['SITE_URL']
    app.config['SHOW_DRAFTS'] = show_drafts

    app.static_folder = project_dir / app.config['STATIC_FOLDER']
    assert app.static_folder is not None
    # To avoid full paths in config.toml
    app.config['FLATPAGES_ROOT'] = (
        project_dir / app.config['POSTS_FOLDER']
    )
    app.config['FREEZER_DESTINATION'] = (
        project_dir / app.config['BUILD_FOLDER']
    )
    app.config['FREEZER_REMOVE_EXTRA_FILES'] = True
    # Allow build to be version controlled
    app.config['FREEZER_DESTINATION_IGNORE'] = ['.git*', '.hg*']
    app.config['FLATPAGES_EXTENSION'] = app.config['POSTS_EXTENSION']

    if Path(app.static_folder).is_dir():
        app.config['INCLUDE_CSS'] = (
            Path(app.static_folder) / 'combined.min.css').exists()
        app.config['INCLUDE_JS'] = (
            Path(app.static_folder) / 'combined.min.js').exists()
    else:
        # During testing they can be True from a previous test
        app.config['INCLUDE_CSS'] = False
        app.config['INCLUDE_JS'] = False

    # Without clearing the cache tests will use templates from the first test
    # Even when the template folder and jinja_loader has changed
    app.jinja_env.cache = {}

    # Allow config settings (even new user created ones) to be used in templates
    for key in app.config:
        app.jinja_env.globals[key] = app.config[key]

    favicon_path = Path(app.static_folder) / 'favicon.svg'
    app.jinja_env.globals['INCLUDE_DEFAULT_FAVICON'] = favicon_path.is_file()

    pages.template_folder = project_dir / app.config['PAGES_FOLDER']

    # Use templates in user set template folder
    # but fallback to app.template_folder (example_site/templates/)
    assert app.jinja_loader is not None
    app.jinja_loader = ChoiceLoader([
        FileSystemLoader(project_dir / app.config['TEMPLATE_FOLDER']),
        # Setting pages.template_folder is not enough
        FileSystemLoader(pages.template_folder),
        app.jinja_loader,
    ])

    posts.init_app(app)
    # Without .reload() posts are from first test
    with app.app_context():
        reload_posts(show_drafts)

    freezer.init_app(app)

    return app
