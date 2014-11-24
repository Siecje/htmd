import os
import shutil
import click
from flask import Flask


@click.group()
def cli():
    pass


def create_directory(name):
    if os.path.isdir(name) is False:
        os.mkdir(name)
        click.echo(click.style('%s was created.' % name, fg='green'))
    else:
        click.echo(click.style('%s already exists and was not created.' % name, fg='red'))


def copy_file(src, dest):
    if os.path.exists(dest) is False:
        shutil.copyfile(src, dest)
        click.echo(click.style('%s was created.' % dest, fg='green'))
    else:
        click.echo(click.style('%s already exists and was not created.' % dest, fg='red'))


@cli.command('start', short_help='Create example files to get started.')
def start():
    create_directory('templates/')
    copy_file(os.path.join(os.path.dirname(__file__), 'templates', '_layout.html'),
          os.path.join('templates/', '_layout.html'))
    create_directory('static/')
    copy_file(os.path.join(os.path.dirname(__file__), 'static', 'reset.css'),
              os.path.join('static/', 'reset.css'))
    copy_file(os.path.join(os.path.dirname(__file__), 'static', 'style.css'),
              os.path.join('static/', 'style.css'))
    create_directory('pages/')
    copy_file(os.path.join(os.path.dirname(__file__), 'about.html'),
              os.path.join('pages/', 'about.html'))
    create_directory('posts/')
    copy_file(os.path.join(os.path.dirname(__file__), 'example.md'),
              os.path.join('posts/', 'example.md'))
    copy_file(os.path.join(os.path.dirname(__file__), 'config.py'),
              os.path.join('config.py'))
    click.echo('Add the site name and edit settings in config.py')


@cli.command('verify', short_help='Verify posts formatting is correct.')
def verify():
    # import is here to avoid looking for the config
    # which doesn't exist until you run start
    from sitebuilder import posts
    correct = True
    for post in posts:
        for item in ['author', 'title', 'date']:
            if item not in post.meta:
                correct = False
                click.echo(click.style('%s does not have %s', post.path, item, fg='red'))
        if 'date' in post.meta:
            try:
                post.meta.get('date').year
            except AttributeError:
                correct = False
                click.echo(click.style('Date %s for %s is not in the format YYYY-MM-DD' % (post.meta.get('date'), post.path), fg='red'))
    if correct is True:
        click.echo(click.style('All posts are correctly formatted.', fg='green'))
        return True
    else:
        return False


@cli.command('build', short_help='Create static version of the site.')
@click.pass_context
def build(ctx):
    valid = ctx.invoke(verify)
    if valid:
        from sitebuilder import freezer, app
        freezer.freeze()
        click.echo(click.style('Static site was created in %s' % app.config.get('FREEZER_DESTINATION'), fg='green'))
    return valid


@cli.command('preview', short_help='Serve files to preview site.')
@click.pass_context
@click.option('--host', '-h', default='127.0.0.1', help='Location to access the files.')
@click.option('--port', '-p', default=9090, help='Port on which to serve the files.')
def preview(ctx, host, port):
    from sitebuilder import app as build_app
    build_app.run(debug=True, host=host, port=port)
    # build static site
    # valid = ctx.invoke(build)
    # if valid is True:
    #     # Serve the build folder
    #     from sitebuilder import app as build_app
    #     app = Flask(__name__, static_folder=os.path.join(os.getcwd(), build_app.config.get('BUILD_FOLDER')))
    #
    #     @app.route('/')
    #     def index():
    #         return app.send_static_file('index.html')
    #
    #     @app.route('/<path:path>')
    #     def serve_index_files(path):
    #         if path.endswith('/'):
    #             return app.send_static_file(os.path.join(path, 'index.html'))
    #         return app.send_static_file(path)
    #
    #     app.run(debug=True, host=host, port=port)
