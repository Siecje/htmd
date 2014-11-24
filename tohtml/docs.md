###Why another static site generator?

I admit I didn't try them [all]. I tried several static site generators written in Python, but I didn't like how complicated they were.
Some issues I had were:
- Too many files and folders
- Too many settings
- I didn't want the generated site to follow the same folder structure as the pages you created.
So if you wanted the date in the URL you need to create a folder for the year, month and date,
instead of having a single directory of all of the posts.
- I didn't want to include all of the templates being, only overwrite the ones I modified.
- It wasn't obvious how to set a value to use in multiple templates.
- If you made changes to one of your templates and ran build you wouldn't update existing files unless you deleted your build folder everytime.



###What is the difference between posts and pages?

Posts are blog posts with dates and authors tracked by feeds. Pages are other pages on the site (About).

###How do I edit the layout of the site?

Edit the ```templates/_layout.html``` file that was created when running ```tohtml start```.
This a [Jinja 2](http://jinja.pocoo.org/docs/dev/templates/#template-inheritance) template that all other pages will use by default.
You can add a link to CSS file that you have created in ```static/```.
To change other pages you will need to override the page template by creating a file with the same name in the ```templates/``` folder.
The complete list of templates can be found [here](TODO: link to templates).
