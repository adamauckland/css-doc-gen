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

	python ./refresh_site.py /path/to/your/scss /path/to/your/finished/styles.css

The styles.css (or whatever your final minified CSS is called) file will get copied across and placed with the documentation.
