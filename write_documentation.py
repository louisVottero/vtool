
class WriteDocumentation(object):
    pass

def get_classes(module):
    classes = []
    
    return classes

def get_definitions(module):
    pass

def get_inherited_classes(module):
    
    parent_module = get_parent_class( module )
    classes = get_classes(module)
    return classes

def get_parent_class( module ):
    pass

def write_info( module ):

    module_help = read_module_info( module )
    
    classes = module.get_classes( module )
    inherited_classes = module.get_inherited_classes( module )
    
    for class_name in inherited_classes:
        if class_name in module_help:
            #write info to html.
            pass
    
    

def read_module_info( module ):
    
    lines = []
    
    for line in lines:
        dict = eval(line)
        
    #key = name of a member of a class
    #dict[key] = information about that member.
    
    return dict