
import sys
import os

import ast
import os

vtool_dir = os.getcwd() + '/python/vtool'

def get_doc_directory():
    
    dir = os.getcwd()

    path = os.path.join(dir, 'docs')
        
    return path

class Parse(object):
    
    def __init__(self, python_file_name):
        
        print('file', python_file_name)
        
        self.filename = python_file_name
        
        self._parse()
        
    def _parse(self):
        
        self.functions = []
        self.classes = []
                
        open_file = open(self.filename, 'r')    
        lines = open_file.read()
        open_file.close()
        
        ast_tree = ast.parse(lines)
        
        last_line_number = 0
        
        for node in ast_tree.body:
            
            inst = None
            
            if isinstance(node, ast.FunctionDef):
                self.functions.append(node.name)
                
            if isinstance(node, ast.ClassDef):
                self.classes.append(node.name)
    
    def get_classes(self):
        return self.classes
    
    def get_functions(self):
        return self.functions
    
class WriteModule(object):
    
    def __init__(self, python_file):
        self.base_dir = None
        self.output_dir = None
        self.python_file = python_file
        
    def _create_class_rst(self, parent):
        
        parent_name = parent.replace('.', '_')
        
        output = self.output_dir
        filename = '%s_classes.rst' % parent_name
        output_file = os.path.join(output, filename)
        
        lines = []
        classes = Parse(self.python_file).get_classes()
        
        if not classes:
            return   
            
        lines.append('Class Summary')
        lines.append('=============')
        lines.append('')
        lines.append('.. currentmodule:: %s' % parent)
        lines.append('')
        lines.append('.. autosummary::')
        lines.append('    :toctree:')
        lines.append('')
        
        for class_name in classes:
        
            lines.append('    %s' % class_name)
            
            full_name = '%s.%s' % (parent, class_name)
            self._create_class_file(full_name)
        
        write_lines(output_file, lines)
        
        return filename
        
    def _get_class_lines(self, class_name):
        
        lines = []
        
        name = class_name.split('.')
        name = name[-1]
        
        lines.append(name)
        lines.append('-' * len(name))
        lines.append('')
        lines.append('    %s' % class_name)
        lines.append('')
        lines.append('.. autoclass:: %s' % class_name)
        lines.append('    :members:')
        lines.append('    :inherited-members:')
        lines.append('    :undoc-members:')
        lines.append('')
        
        return lines
        
    def _create_class_file(self, class_name): 
    
        output = self.output_dir
        filename = '%s.rst' % class_name
        output_file = os.path.join(output, filename)
        
        lines = self._get_class_lines(class_name)
        
        print( output_file)
        
        write_lines(output_file, lines)
        
        return filename
    
    def _create_functions_rst(self,parent):
        
        parent_name = parent.replace('.', '_')
        
        output = self.output_dir
        filename = '%s_functions.rst' % parent_name
        output_file = os.path.join(output, filename)
        
        
        lines = []
        functions = Parse(self.python_file).get_functions()
        
        if not functions:
            return
            
        lines.append('Function Summary')
        lines.append('================')
        lines.append('')
        lines.append('.. currentmodule:: %s' % parent)
        lines.append('')
        lines.append('.. autosummary::')
        lines.append('')
        
        for function in functions:
            lines.append('    %s' % function)
        
        lines.append('')
        lines.append('.. rubric:: Functions')
        lines.append('')
        
        for function in functions:
            lines.append('.. autofunction:: %s' % function)
            lines.append('')
            
        parent_name = parent.replace('.', '_')
        
        current_directory = os.getcwd()
        
        write_lines(output_file, lines)
        
        return filename
    
    def _create_combine_rst(self, parent):
    
        parent_name = parent.replace('.', '_')
        
        output = self.output_dir
        filename = '%s_summary.rst' % parent_name
        output_file = os.path.join(output, filename)
        
        
        lines = []
        functions = Parse(self.python_file).get_functions()
        classes = Parse(self.python_file).get_classes()
        
        lines.append('')
        lines.append('.. currentmodule:: %s' % parent)
        lines.append('')
        
        
        if classes:
        
            lines.append('')
            lines.append('.. rubric:: Class Summary')
            lines.append('')
        
            lines.append('')
            lines.append('.. autosummary::')
            #lines.append('    :toctree:')
            lines.append('')
            
            for class_name in classes:
                
                lines.append('    %s' % class_name)
                
                #full_name = '%s.%s' % (parent, class_name)
                
                #class_lines = self._get_class_lines(class_name)
                #lines += class_lines
                
                #self._create_class_file(full_name)            
        
        if functions:

            lines.append('')
            lines.append('.. rubric:: Function Summary')
            lines.append('')
        
            lines.append('')      
            lines.append('.. autosummary::')
            lines.append('')
        
            for function in functions:
                lines.append('    %s' % function)
            """
            lines.append('')
            lines.append('.. rubric:: Functions')
            lines.append('')
        
            for function in functions:
                lines.append('.. autofunction:: %s' % function)
                lines.append('')
            """
            
        lines.append('')
        lines.append('.. automodule:: %s' % parent)
        lines.append('    :members:')
        lines.append('    :inherited-members:')
        lines.append('    :undoc-members:')
        lines.append('')
        
        #parent_name = parent.replace('.', '_')
        
        return lines
    
    def set_output_dir(self, dirname):
        self.output_dir = dirname
        
    def set_base_dir(self, dirname):
        self.base_dir = dirname
    
    def create_module_rst(self, name, parent):
        
        parent_name = parent.replace('.', '_')
        
        filename = parent_name + '_' + name
        
        output = self.output_dir
        output_file = os.path.join(output, '%s.rst' % filename)
        
        lines = []
        
        title_name = parent + '.' + name
        
        lines.append(title_name)
        lines.append('-' * len(title_name))
        lines.append('')
        
        sub_parent = parent + '.' + name 
        
        sub_lines = self._create_combine_rst(sub_parent)
        
        if sub_lines:
            lines += sub_lines
            
        write_lines(output_file, lines)
    
        
def write_lines(filename, lines):
    
    open_file = open(filename, 'w')
    
    try:
        for line in lines:
            open_file.write('%s\n' % line)
    except:
        pass
    
    open_file.close()
    
    