import os
import os.path
import sys


class CssItem(object):
    def __init__(self):
        self.selector = None
        self.comments = {}
        self.definition = None
        self.atom = None

    def __str__(self):
        return 'Element: %s\n%s\n%s\nAtom:\n%s' % (self.selector, self.comments, self.definition, self.atom)


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
        for loop_character in data:
            self.chomp(loop_character)

    def chomp(self, character):
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
        self.selector_text = ''.join(self.selector)
        self.definition_text = ''.join(self.definition)

        self.look_for_comments()

        css_item = CssItem()
        css_item.atom = ''.join(self.buffer)
        css_item.selector = '\n'.join(self.finished_selector_buffer)
        css_item.comments = self.comment_buffer
        css_item.definition = self.definition_text

        self.chomp_stack.append(css_item)

        #
        # look for anything inside me
        #
        #css_object = CssChomper(self.chomp_stack)
        #css_object.parse(self.definition_text)

        #print('\n\nselector %s' % '\n'.join(self.finished_selector_buffer))
        #print('Comment buffer: %s' % self.comment_buffer)
        #print('definition  { %s }' % self.definition_text)

    def look_for_comments(self):
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
            else:
                self.finished_selector_buffer.append(line)


class ParseReader(object):
    def __init__(self):
        self.comment_buffer = {}
        self.css_match_buffer = []
        self.css_objects = []

    def parse_doc(self, filename, data):
        self.log(filename)
        chomp_stack = []

        css_object = CssChomper(chomp_stack)
        css_object.parse(data)

        for loop_item in chomp_stack:
            if len(loop_item.comments) > 0:
                print(loop_item)

        #self.log(data)


    def parse_line(self, original_line):
        #self.log('Parse: %s' % original_line)

        line = original_line
        comment_index = line.find('//')
        open_brace_index = line.find('{')

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

                #self.log('\t\t%s --> %s' % (at_key, at_value))
                self.comment_buffer[at_key] = at_value

        #
        # Push output onto stack
        if line.find('}') != -1:
            if len(self.comment_buffer) > 0:
                new_object = CssObject()
                new_object.comments = self.comment_buffer
                self.css_objects.append(new_object)

            self.comment_buffer = {}


class CssDoc(object):
    def parse(self, root_directory):
        self.log('Parsing directory: %s' % root_directory)
        files = {}
        self.scan_directory(files, root_directory, root_directory)

        for loop_key, loop_item in files.items():
            self.parse_file(loop_key, loop_item)

    def scan_directory(self, files, root_directory, new_directory):
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
        print('Pass in the root of SCSS ')
    else:
        root_directory = sys.argv[1]
        css_doc = CssDoc()
        css_doc.log = log
        css_doc.parse(root_directory)
