import os
import os.path
import sys


class ParseReader(object):
    def __init__(self):
        self.comment_buffer = {}
        self.css_match_buffer = []

    def parse_line(self, original_line):
        self.log('Parse: %s' % original_line)

        line = original_line
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

                self.log('\t\t%s --> %s' % (at_key, at_value))
                self.comment_buffer[at_key] = at_value


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
        for loop_line in loop_data.split('\n'):
            parser.parse_line(loop_line)


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
