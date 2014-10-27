import sys

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "start":
        import os
        os.mkdir('templates')
        os.mkdir('pages')
        os.mkdir('posts')
        with open('config.py', 'w') as config_file:
            config_file.write("""import os
DEBUG = True
FLATPAGES_AUTO_RELOAD = DEBUG
FLATPAGES_EXTENSION = '.md'
FLATPAGES_ROOT = 'posts'
FREEZER_DESTINATION = os.path.join(os.getcwd() + '/build')

SITE_NAME = ''
SHOW_AUTHOR = True
""")
    elif len(sys.argv) > 1 and sys.argv[1] == "build":
        from sitebuilder import freezer
        freezer.freeze()
    else:
        from sitebuilder import app
        app.run(port=5000)
