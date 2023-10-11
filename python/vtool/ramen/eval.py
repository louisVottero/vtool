from .. import util, util_file
from .ui_lib import ui_nodes
from . import rigs 



def run(json_file):
    watch = util.StopWatch()
    watch.start('Ramen Graph')
    util.show('Run Eval ------------------------------')
    visited = {}
    in_connections = {}
    
    json_data = util_file.get_json(json_file)
    
    connections = []
    items = {}
    start_eval_items = {}
    eval_items = {}
    start_items = {}
    
    
    util.show('Gathering Data ------------------------------')
    for item_dict in json_data:
        item_type = item_dict['type']
        if item_type in ui_nodes.register_item: 
            node = ui_nodes.register_item[item_type]()
            node.load(item_dict)
            uuid = item_dict['uuid']
            items[uuid] = node
        
            inputs = node.rig.get_ins()
            for input_name in inputs:
                
                if input_name.find('Eval') > -1:

                    if hasattr(node, 'rig_type'):
                        eval_items[uuid] = node
                    else:
                        start_eval_items[uuid] = node
                    break
            
            if not inputs:
                start_items[uuid] = node
            
        if item_dict['type'] == 4:
            connections.append(item_dict)
    
    ui_nodes.uuids = items
    
    for connection in connections:
        line_inst = ui_nodes.NodeLine()
        line_inst.load(connection)
    connections = []
    
    util.show('Running Eval items ------------------------------')
    
    for uuid in start_eval_items:
        if uuid in visited:
            continue
        node = start_eval_items[uuid]
        if not node:
            continue
        node.run()
        
        visited[uuid] = None
        
    for uuid in eval_items:
        if uuid in visited:
            continue
        node = eval_items[uuid]
        if not node:
            continue
        node.run()
        
        visited[uuid] = None

    util.show('Running Start Items ------------------------------')
    for uuid in start_items:
        if uuid in visited:
            continue
        node = start_items[uuid]
        node.run()
        
        visited[uuid] = None

    util.show('Running Items ------------------------------')
    for uuid in items:
        if not uuid in in_connections:
            continue
        
        if uuid in visited:
            continue
        
        node = items[uuid]
        node.run()
        
        visited[uuid] = None
    
    util.show('Finished Graph')
    watch.end()
def remove():
    rigs.remove_rigs()