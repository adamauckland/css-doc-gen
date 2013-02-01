import os
import os.path
import sys


class CssItem(object):
    """
    This object generates some output for one single atom of CSS.

    What is an atom? A single bit of comment + CSS selector + CSS definition.

    The comments are expected to hold the tags in.

    The selector could be any sort of CSS. Examples of valid selectors:

        a, br, hr

        p

        .main, .stuff

    Currently, multi-line example comments are not supported. I'm not really sure how the parser will handle them

    """
    known_comment_tags = ['description', 'example', 'version', 'class']

    def __init__(self):
        self.selector = None
        self.comments = {}
        self.definition = None
        self.atom = None

    def __unicode__(self):
        """
        Generate the documentation for this CssItem
        """
        context = {
            'selector': self.selector,
            'comments': self.comments,
            'definition': self.definition,
            'atom': self.atom,
        }

        #
        # set defaults
        #
        for tag in CssItem.known_comment_tags:
            context['comments_%s' % tag] = ''
        #
        # unpack comments
        #
        # This will unpack all available comments in the declaration into
        # comments_THINGYHERE
        #
        for loop_key, loop_value in self.comments.items():
            context['comments_%s' % loop_key] = loop_value

        template = """
            <div>
                <h2> %(selector)s </h2>

                <div>
                    <h3>Description</h3>
                    <p>%(comments_description)s </p>
                </div>

                <div>
                    <h3>Example</h3>
                    %(comments_example)s
                </div>

                <div>
                    <h3>How to do it</h3>
                    <code><xmp>%(comments_example)s </xmp></code>
                </div>

            </div>

        """

        return template % context


class CssChomper(object):
    def __init__(self, chomp_stack):
        self.chomp_stack = chomp_stack
        self.reset()

    def reset(self):
        self.comment_buffer = {}
        self.buffer = []
        self.entry_count = 0
        self.in_comments = False
        self.selector = []
        self.definition = []
        self.entered_definition = False
        self.finished_selector_buffer = []

    def __repr__(self):
        return repr(self.comments)

    def parse(self, data):
        """
        Feed the parser with the characters from the buffer
        """
        for loop_character in data:
            self.chomp(loop_character)

    def chomp(self, character):
        """
        Read a character and do something with it
        """
        self.buffer.append(character)

        is_control_character = False

        if character == '{':
            is_control_character = True
            self.entered_definition = True
            self.entry_count += 1

        if character == '}':
            #
            # Hack to add final }
            #
            self.definition.append(character)

            is_control_character = True
            self.entry_count -= 1
            #
            # Reached end
            #
            if self.entry_count == 0:
                self.output()

        if not is_control_character:
            if not self.entered_definition:
                self.selector.append(character)

        if self.entered_definition:
            self.definition.append(character)

    def output(self):
        """
        Add all the details for the CssItem onto the stack
        """
        self.selector_text = ''.join(self.selector)
        self.definition_text = ''.join(self.definition)

        self.look_for_comments()

        css_item = CssItem()
        css_item.atom = ''.join(self.buffer)
        css_item.selector = '\n'.join(self.finished_selector_buffer)
        css_item.comments = self.comment_buffer
        css_item.definition = self.definition_text

        self.chomp_stack.append(css_item)

    def look_for_comments(self):
        """
        Look for any comments in the selector block and attempt to parse
        into [@key value] pairs.

        If a line contains a comment and no @key, attempt to concatenate
        onto the last found key.
        """
        last_key = None
        for line in self.selector_text.split('\n'):
            comment_index = line.find('//')
            #
            # Found a comment
            #
            if comment_index > -1:
                line = line[comment_index + 2:]
                at_index = line.find('@')
                if at_index != -1:
                    at_split = line.split('@')

                    at_key = at_split[1].split(' ')[0].strip()
                    at_value = line[at_index + len(at_key) + 1:].strip()

                    self.comment_buffer[at_key] = at_value
                    last_key = at_key
                else:
                    if last_key:
                        self.comment_buffer[last_key] += '\n' + line
            else:
                self.finished_selector_buffer.append(line)


class ParseReader(object):
    def __init__(self):
        self.comment_buffer = {}
        self.css_match_buffer = []
        self.css_objects = []

    def parse_doc(self, filename, data):
        """
        Generate documentation for data.

        Note: filename is considered a relative filename from the script location,
        not the full filename.
        """
        self.log(filename)
        chomp_stack = []

        css_object = CssChomper(chomp_stack)
        css_object.parse(data)

        internal_items = []

        for loop_item in chomp_stack:
            if len(loop_item.comments) > 0:
                internal_items.append(unicode(loop_item))

        output = """
        <html>
            <head>
                <link rel="stylesheet" href="style.css" />
            </head>
            <body>
                <div>File: %s</div>
                <div>%s</div>
            </body>
        </html>

        """ % (filename, '\n'.join(internal_items))

        if len(internal_items) > 0:
            output_directory = os.path.abspath('./output')
            output_file = os.path.join(output_directory, filename.replace('/', '_') + '.html')

            with open(output_file, 'wt') as output_handle:
                output_handle.write(output)


class CssDoc(object):
    def parse(self, root_directory, css_file):
        output_directory = os.path.abspath('./output')
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        with open(css_file, 'rt') as read_handle:
            read_buffer = read_handle.read()
            with open(os.path.join(output_directory, 'style.css'), 'wt') as write_handle:
                write_handle.write(read_buffer)

        self.log('Parsing directory: %s' % root_directory)
        files = {}
        self.scan_directory(files, root_directory, root_directory)

        for loop_key, loop_item in files.items():
            self.parse_file(loop_key, loop_item)

    def scan_directory(self, files, root_directory, new_directory):
        """
        Scan a directory for SCSS files
        """
        try:
            for loop_file in os.listdir(new_directory):
                loop_filename = os.path.join(new_directory, loop_file)
                if os.path.isdir(loop_filename):
                    self.scan_directory(files, root_directory, loop_filename)
                if os.path.isfile(loop_filename):
                    with open(loop_filename, 'rt') as file_handle:
                        read_buffer = file_handle.read()
                    file_key = loop_filename[len(root_directory):]
                    files[file_key] = read_buffer
                    bytes = len(read_buffer)
                    self.log('\t%s  (%s bytes)' % (file_key, bytes))
        except Exception, ex:
            self.log('Exception %s' % ex)

    def parse_file(self, loop_key, loop_data):
        parser = ParseReader()
        parser.log = self.log
        parser.parse_doc(loop_key, loop_data)


def log(text):
    print(text)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Pass in the root of SCSS and filepath to css file ')
    else:
        root_directory = sys.argv[1]
        css_doc = CssDoc()
        css_doc.log = log
        css_doc.parse(root_directory, sys.argv[2])
