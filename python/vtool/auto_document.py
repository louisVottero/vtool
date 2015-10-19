import inspect

import util_file

class CreateHtml(object):
    
    def __init__(self, name, filepath):
        
        self.name = name
        self.filepath = filepath
    
        self.header_title_string = ''
        self.css_link = ''
        
        self.blocks = []
        
    
    def _create_lines(self):
        lines = []
        
        lines.append('<!DOCTYPE html>')
        lines.append('<html>')
        lines.append('    <head>')
        if self.header_title_string:
            lines.append('        <title> %s </title>' % self.header_title_string )
        if self.css_link:
            lines.append('        <link rel = "stylesheet" type = "text/css" href = "%s">' % self.css_link )
        lines.append('    </head>')
        lines.append('    <body>')
        
        for block in self.blocks:
            lines.append(block)
        
        lines.append('    </body>')
        lines.append('</html>')
        
        return lines
        
    def _create_file(self, lines):
        
        new_filepath = util_file.create_file(self.name, self.filepath)
        util_file.write_lines(new_filepath, lines)
        
    def _create_block(self, indent, prefix, text):
        indent_str = 8 * ' '
        block = '%s<%s> %s </%s>' % (indent_str, prefix, text, prefix)
        return block
        
    def set_header_title(self, string):
        self.header_title_string = string
    
    def set_css_link(self, css_link_string):
        self.css_link = css_link_string
    
    def add_header(self, text, header_number = 1):
        text = self._create_block(8, 'h%s' % header_number, text)
        self.blocks.append(text)
    
    def add_paragraph(self, text):
        text = self._create_block(8, 'p', text)
        self.blocks.append(text)
    
    def create(self):
        
        lines = self._create_lines()
        self._create_file(lines)
        

class CreatePythonModuleHtml(CreateHtml):
    
    def __init__(self, name, filepath):
        super(CreatePythonModuleHtml, self).__init__(name, filepath)
        
        self.python_filepath = ''
    
    def _get_header(self, header_object):
        
        name = header_object.get_name()
        args = header_object.get_args()
                
        header = '%s (%s)' % (name, args)
        
        return header
    
    def set_python_module(self, filepath):
        self.python_filepath = filepath
        
    def create(self):
        
        if util_file.is_file(self.python_filepath):
            parse = ParsePython(self.python_filepath)
            
            for class_object in parse.get_classes():
                
                header = self._get_header(class_object)
                header = 'Class %s' % header
                self.add_header(header, '2')
                self.add_paragraph(class_object.get_doc_string())
                
            for class_object in parse.get_functions():
                
                header = self._get_header(class_object)
                header = 'Function %s' % header
                self.add_header(header, '2')
                self.add_paragraph(class_object.get_doc_string())
                
        super(CreatePythonModuleHtml, self).create()

class ParsePython(object):
    
    def __init__(self, python_file_name):
        
        self.filename = python_file_name
        
        self.module = util_file.source_python_module(self.filename)
        
        self.classes = []
        self.functions = []
        
        self._parse()
        
    def _parse(self):
        
        self.functions = []
        self.classes = []
        
        self.contents = dir(self.module)
        
        for content in self.contents:
            
            print content
            
            object_inst = None
            
            exec('object_inst = self.module.%s' % content)
            
            inst = None
            
            if inspect.isfunction(object_inst):
                inst = ObjectFunctionData(object_inst)
                self.functions.append(inst)
                
            if inspect.isclass(object_inst):
                inst = ObjectClassData(object_inst)
                self.classes.append(inst)
                
    def get_classes(self):
        return self.classes
    
    def get_functions(self):
        return self.functions

class ObjectData(object):
    
    def __init__(self, object_inst):
        self.object_inst = object_inst
    
    def get_name(self):
        name = self.object_inst.__name__
        return name
    
    def get_doc_string(self):
        doc = self.object_inst.__doc__
        return doc
    
class ObjectFunctionData(ObjectData):
    
    def get_args(self):
        
        args = get_args(self.object_inst)
        
        return args
    
class ObjectClassData(ObjectData):
    
    def get_args(self):
        
        args = None
        
        print 'get class args', self.get_name()
        try:
            args = get_args(self.object_inst.__init__)
        except:
            #does not have __init__
            args = None
        
        return args
        
def get_args(object_inst):
    
    args = inspect.getargspec(object_inst)
    
    if not args.args:
        return
    
    print args.args
    print args.defaults
    
    defaults = {}
    
    if args.defaults:
        defaults = dict( zip(reversed(args.args), reversed(args.defaults)) )
    
    
    
    ordered_args = []
    
    for arg in args.args:
        
        arg_value = arg
    
        print 'defaults!', defaults, type(defaults)
        if defaults:    
            if defaults.has_key(arg):
                arg_value = (arg, defaults[arg])
            
        ordered_args.append(arg_value)
        
    return ordered_args
    
        