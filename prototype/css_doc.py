#!/usr/bin/env python
# coding=utf-8
# Copyright (c) 2013 Adam Auckland
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import os
import os.path
import sys
import jinja2
import shutil


class CssItem(object):
    """
    This object generates some output for one single atom of CSS.

    What is an atom? A single bit of comment + CSS selector + CSS definition.

    The comments are expected to hold the tags in.

    The selector could be any sort of CSS. Examples of valid selectors:

        a, br, hr

        p

        .main, .stuff

    Currently, multi-line example comments are not supported.
    I'm not really sure how the parser will handle them

    """
    known_comment_tags = [
        'description', 'example', 'version', 'class',
        'author', 'type', 'notes', 'date', 'section',
        'main_description'  # if there is no tag, assume it's the top description
    ]

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

                <div> %(main_description)s </div>

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
        last_key = 'main_description'
        self.comment_buffer[last_key] = ''
        is_in_comments = False
        for line in self.selector_text.split('\n'):
            comment_index = line.find('//')
            block_comment_index = line.find('/*')

            if block_comment_index > comment_index:
                comment_index = block_comment_index
                is_in_comments = True

            if is_in_comments:
                if line.find('*/') != -1:
                    line = line[line.find('*/') + 2:]
                    is_in_comments = False
                    comment_index = -1
                    block_comment_index = -1
                else:
                    if line.find('*') != -1:
                        comment_index = line.find('*')
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

    def parse_doc(self, filename, data, SETTINGS):
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
                loop_item.filename = filename
                internal_items.append(loop_item)

        return internal_items


class Partial(object):
    def __init__(self, partial_name):
        self.partial_name = partial_name
        self.items = []


class CssDoc(object):
    def parse(self, SETTINGS):
        root_directory = SETTINGS.SCSS_ROOT
        css_files = SETTINGS.CSS_FILES
        SETTINGS.CSS_OUTPUT_FILES = []
        template_file = SETTINGS.JINJA2_TEMPLATE_FILE

        with open(template_file, 'rt') as template_handle:
            SETTINGS.template_data = template_handle.read()
            print('read template')

        output_directory = os.path.abspath('./output')
        self.log('Output to %s' % output_directory)
        shutil.rmtree(output_directory)

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        file_index = 0
        for css_file in css_files:
            file_index += 1
            with open(css_file, 'rt') as read_handle:
                read_buffer = read_handle.read()
                css_output_file = 'style%s.css' % file_index

                with open(os.path.join(output_directory, css_output_file), 'wt') as write_handle:
                    write_handle.write(read_buffer)
                    SETTINGS.CSS_OUTPUT_FILES.append(css_output_file)
                    print('%s --> %s' % (css_file, css_output_file))

        self.log('Parsing directory: %s' % root_directory)
        files = {}
        self.scan_directory(files, root_directory, root_directory)

        items = []
        for loop_key, loop_item in files.items():
            partial = Partial(loop_key)
            partial.items = self.parse_file(loop_key, loop_item, SETTINGS)
            if len(partial.items) > 0:
                items.append(partial)

        #
        # now output
        #
        template_instance = jinja2.Template(SETTINGS.template_data)
        output = template_instance.render({
            'items': items,
            'settings': SETTINGS
        })

        if len(items) > 0:
            output_directory = os.path.abspath('./output')
            output_file = os.path.join(output_directory, 'output.html')

            with open(output_file, 'wt') as output_handle:
                output_handle.write(output)
        #
        # copy assets over
        #
        self.log('Copying assets')
        for asset_dir in SETTINGS.ASSETS:
            asset_dir_name = asset_dir[asset_dir.rfind('/') + 1:]
            self.log('%s --> %s' % (asset_dir, os.path.abspath('./output/%s' % asset_dir_name)))
            shutil.copytree(asset_dir, os.path.abspath('./output/%s' % asset_dir_name))

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

    def parse_file(self, loop_key, loop_data, SETTINGS):
        parser = ParseReader()
        parser.log = self.log
        return parser.parse_doc(loop_key, loop_data, SETTINGS)


def log(text):
    print(text)


if __name__ == '__main__':
    import imp
    settings_file = os.path.abspath('./cssdoc_settings.py')

    SETTINGS = imp.load_source('SETTINGS', settings_file)
    css_doc = CssDoc()
    css_doc.log = log
    css_doc.parse(SETTINGS)
