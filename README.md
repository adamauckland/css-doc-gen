css-doc-gen
===========

Generate useful documentation from CSS. This is in no way a finished product, just a starting point. The script assumes SCSS at the moment.

Requirements
------------

Currently uses [Jinja2](http://jinja.pocoo.org/docs/) for the templating. Install it by doing either:

	easy_install Jinja2
	pip install Jinja2

Annotate your SCSS
------------------

Use a JSDoc style commenting system to apply tags to your CSS. Currently supported tags:

	@description
	@example
	@version
	@class
	@author
	@type
	@notes
	@date
	@section

@example supports multiple lines

Here is an example of some annotated SCSS:

	/**
	 * You can put untagged comments and they will still appear
	 *
	 * @description Creates the styling for the site page title
	 *
	 * @author Benny Crivens
	 * @version 0.1
	 * @date 2013-01-31
	 *
	 * @example
	 * <h2 class="pageTitle">An example pagetitle usage</h2>
	 *
	 * @type layout class
	 * @notes
	 */
	.layoutFooter {
		clear: both;
		@include content-container;
		.layoutWrapper {
			margin-top: 1em;
			padding: 1em;
			text-align: center;
		}
	}


Running the generator
---------------------

	Simply call css_doc.py from a directory containing a cssdoc_settings.py file

Settings file
-------------

Create a file called cssdoc_settings.py where you want your documentation generated.
By default, it will create a directory next to this file called 'output'

	#
	# Full path to the root of your SCSS
	#
	SCSS_ROOT = ''
	#
	# A list of full paths of CSS files to import in the template
	#
	CSS_FILES = ['', ]
	#
	# List of full paths to any assets directories to get copied into output
	#
	ASSETS = ['', ]
	#
	# Template to generate output HTML with. If not specified, the one with css_doc.py is used instead
	#
	# JINJA2_TEMPLATE_FILE = 'template.html'


The styles.css (or whatever your final minified CSS is called) file will get copied across and placed with the documentation.
