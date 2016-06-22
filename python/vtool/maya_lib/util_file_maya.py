# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import util_file
import re

def clean_place_holder_list_entries(filepath):
    
    filepath = util_file.fix_slashes(filepath)

    base_path = util_file.get_dirname(filepath)
    new_path = util_file.join_path(base_path, 'cleaned.ma')

    util_file.copy_file(filepath, new_path)
    
    lines = util_file.get_file_lines(filepath)
    
    phl_lines = {}
    bad_phl_slots = {}
    reference_node = None
    bad_inc = []
    
    for inc in range(0, len(lines)):
        
        if lines[inc].find('.phl') == -1:
            if reference_node:
                reference_node = None
            continue
        
        if inc > 0:
            
            reference_node_before = reference_node
            
            reference_node = check_for_phl_reference_node(lines[inc], lines[inc-1])
            
            if reference_node and reference_node != 'skip':
                phl_lines[reference_node] = []
                continue
            
            if reference_node == 'skip':
                reference_node = reference_node_before
                continue
            
            if not reference_node:
                reference_node = reference_node_before
        
        inputs = lines[inc].split('"')[1::2]
        
        if len(inputs) == 1 and reference_node:
            
            numbers = re.findall('[0-9]+', lines[inc])
            
            if reference_node:
                phl_lines[reference_node].append([numbers[0], inc])
                    
        if lines[inc].count('RN') == 2 and lines[inc].count('.phl[') == 2:
            reference_node1 = inputs[0].split('.')[0]
            reference_node2 = inputs[1].split('.')[0]
            
            
            if reference_node1 == reference_node2:
                if not bad_phl_slots.has_key(reference_node1):
                    bad_phl_slots[reference_node1] = []
                   
                
                number1 = re.findall('[0-9]+', inputs[0])
                number2 = re.findall('[0-9]+', inputs[1])
                
                bad_phl_slots[reference_node1].append(number1)
                bad_phl_slots[reference_node1].append(number2)
                
                bad_inc.append(inc)
        
    
    """
    print 'checking bad lines...'
                
    for reference_node in bad_phl_slots:
        
        print 'checking reference node %s' % reference_node
        
        if reference_node == None:
            continue
        
        inputs = bad_phl_slots[reference_node]
        
        for input_value in inputs:
            
            for line in phl_lines[reference_node]:
            
                if line[0] == input_value:
                    bad_inc.append(line[1])    
    """
    good_lines = lines
    
    print 'writing to file...'
    
    bad_inc.reverse()
    
    for inc in bad_inc:
        
        good_lines.pop(inc)        
        
    util_file.write_lines(new_path, good_lines)
    
    return
    
def check_for_phl_reference_node(line, parent_line):
    
    match = re.search("setAttr -s [0-9]+ \".phl\";", line)
    
    reference_node = None
    
    if hasattr(match, 'group'):
             
        reference_node = 'skip'
                
        quotes = parent_line.split('"')[1::2]
        
        if quotes:
            reference_node = quotes[-1]
            
    return reference_node