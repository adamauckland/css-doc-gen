css-doc-gen
===========

Useful documentation from CSS. This is in no way a finished product, just a starting point. The script assumes SCSS at the moment.

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

Example supports multiple lines.

Usage:

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
