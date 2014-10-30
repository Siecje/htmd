import shutil
import sys


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "start":
        import os
        os.mkdir('templates')
        os.mkdir('static')
        os.mkdir('pages')
        os.mkdir('posts')
        shutil.copy(os.path.join(os.path.dirname(__file__), 'config.py'),
                    os.getcwd())
        shutil.copy(os.path.join(os.path.dirname(__file__), 'templates', '_layout.html'),
                    os.path.join(os.getcwd(), 'templates/'))
        shutil.copy(os.path.join(os.path.dirname(__file__), 'static', 'reset.css'),
                    os.path.join(os.getcwd(), 'static/'))
        shutil.copy(os.path.join(os.path.dirname(__file__), 'static', 'style.css'),
                    os.path.join(os.getcwd(), 'static/'))
        shutil.copy(os.path.join(os.path.dirname(__file__), 'about.html'),
                    os.path.join(os.getcwd(), 'pages/'))
        shutil.copy(os.path.join(os.path.dirname(__file__), 'example.md'),
                    os.path.join(os.getcwd(), 'posts/'))
    elif len(sys.argv) > 1 and sys.argv[1] == "build":
        from sitebuilder import freezer
        freezer.freeze()
    else:
        from sitebuilder import app
        app.run(port=5000)
