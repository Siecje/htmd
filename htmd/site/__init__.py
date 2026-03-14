from pathlib import Path
import sys
import tomllib
import typing

from flask import current_app, Flask, send_from_directory
from flask.typing import ResponseReturnValue
from jinja2 import ChoiceLoader, FileSystemLoader

from ..constants import CONFIG_FILE
from ..utils import get_static_files, minify_css_files, minify_js_files
from .freezer import freeze_bp, freezer
from .main import main_bp
from .pages import pages
from .posts import create_posts_blueprint


def get_project_dir() -> Path:
    current_directory = Path.cwd()

    while not (current_directory / CONFIG_FILE).is_file():
        parent_directory = current_directory.parent

        if current_directory == parent_directory:
            return Path.cwd()

        current_directory = parent_directory

    return current_directory


def custom_static(filename: str) -> ResponseReturnValue:
    assert current_app.static_folder is not None
    suffix = Path(filename).suffix
    if suffix == '.css':
        directory = current_app.config.get('static_dir_css', current_app.static_folder)
    elif suffix == '.js':
        directory = current_app.config.get('static_dir_js', current_app.static_folder)
    else:
        directory = current_app.static_folder
    return send_from_directory(directory, filename)


def toml_config_get(
    cfg: dict[str, typing.Any],
    section: str,
    key: str,
    default: typing.Any,  # noqa: ANN401
) -> typing.Any:  # noqa: ANN401
    node = cfg
    for part in section.split('.'):
        node = node.get(part, {})
    try:
        return node.get(key, default)
    except AttributeError:
        return default


def create_app(  # noqa: PLR0915
    *,
    show_drafts: bool = False,
    minify_css: bool = True,
    minify_js: bool = True,
) -> Flask:
    this_dir = Path(__file__).parent
    app = Flask(
        __name__,
        # To prevent default static endpoint from being added to app
        static_folder=None,
        # default templates
        template_folder=this_dir / '..' / 'example_site' / 'templates',
    )

    project_dir = get_project_dir()

    try:
        with (project_dir / CONFIG_FILE).open('rb') as config_file:
            htmd_config = tomllib.load(config_file)
    except FileNotFoundError:
        msg = f'Can not find {CONFIG_FILE}'
        sys.exit(msg)

    # Flask configs are flat, config.toml is not
    # Define the configuration keys and their default values
    # 'Flask config': [section, key, default]
    config_keys: dict[str, tuple[str, str, typing.Any]] = {
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

        'PRETTY_HTML': ('html', 'pretty', False),
        'MINIFY_HTML': ('html', 'minify', False),

        'POSTS_EXTENSION': ('posts', 'extension', '.md'),
        'POSTS_BASE_PATH': ('posts', 'base_path', '/blog/'),

        'SHOW_AUTHOR': ('posts.author', 'show', True),
        'DEFAULT_AUTHOR': ('posts.author', 'default_name', ''),
        'DEFAULT_AUTHOR_TWITTER': ('posts.author', 'default_twitter', ''),
        'DEFAULT_AUTHOR_FACEBOOK': ('posts.author', 'default_facebook', ''),

        'FLATPAGES_MARKDOWN_EXTENSIONS': ('posts.markdown', 'extensions', None),

        'PAGEFIND_OUTPUT': ('pagefind', 'output', 'pagefind'),
        'PAGEFIND_EXCLUDE_SELECTORS': (
            'pagefind',
            'exclude_selectors',
            ['nav', 'footer', '.post-preview'],
        ),
        'PAGEFIND_KEEP_INDEX_URL': ('pagefind', 'keep_index_url', False),
    }

    # Update app.config using the configuration keys
    for flask_key, (table, key, default) in config_keys.items():
        app.config[flask_key] = toml_config_get(htmd_config, table, key, default)

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

    # Without clearing the cache tests will use templates from the first test
    # Even when the template folder and jinja_loader has changed
    app.jinja_env.cache = {}

    # Allow config settings (even new user created ones)
    # to be used in templates
    for key in app.config:
        app.jinja_env.globals[key] = app.config[key]

    static_src_root = Path(app.static_folder)
    css_paths = get_static_files(static_src_root, '.css')
    if minify_css:
        static_source_dir = project_dir / app.config['BUILD_FOLDER'] / 'static'
        static_source_dir.mkdir(parents=True, exist_ok=True)
        app.config['static_dir_css'] = static_source_dir
        files_css = minify_css_files(
            static_src_root,
            css_paths,
            static_source_dir,
        )
    else:
        files_css = [str(path) for path in css_paths]

    js_paths = get_static_files(static_src_root, '.js')
    if minify_js:
        static_source_dir = project_dir / app.config['BUILD_FOLDER'] / 'static'
        static_source_dir.mkdir(parents=True, exist_ok=True)
        app.config['static_dir_js'] = static_source_dir
        files_js = minify_js_files(
            static_src_root,
            js_paths,
            static_source_dir,
        )
    else:
        files_js = [str(path) for path in js_paths]

    favicon_path = static_src_root / 'favicon.svg'

    app.jinja_env.globals.update({
        'FILES_CSS': files_css,
        'FILES_JS': files_js,
        'MINIFY_CSS': minify_css,
        'MINIFY_JS': minify_js,
        'INCLUDE_DEFAULT_FAVICON': favicon_path.is_file(),
    })

    app.config.update({
        'MINIFY_CSS': minify_css,
        'MINIFY_JS': minify_js,
    })

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

    app.add_url_rule(
        '/static/<path:filename>',
        endpoint='static',
        view_func=custom_static,
    )

    # Register freezer blueprint so /404.html exists for frozen builds
    app.register_blueprint(freeze_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(pages)

    # Create a fresh blueprint and Posts instance for this app
    posts_base_path = app.config.get('POSTS_BASE_PATH', '/blog/')
    posts_bp, posts = create_posts_blueprint(posts_base_path)
    app.register_blueprint(posts_bp)

    posts.init_app(app)
    # populate publish_posts
    with app.app_context():
        posts.reload(show_drafts=show_drafts)

    freezer.init_app(app)

    return app


# Explicitly export everything for mypy
__all__ = [
    'create_app',
    'freezer',
    'pages',
]
