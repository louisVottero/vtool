from .. import util_file
from .ui_lib import ui_nodes
from ..maya_lib2 import rigs 

visited = {}
in_connections = {}

def run(json_file):
    
    json_data = util_file.get_json(json_file)
    
    connections = []
    items = {}
    eval_items = {}
    start_items = {}
    
    for item_dict in json_data:
        item_type = item_dict['type']
        print(item_dict)
        if item_type in ui_nodes.register_item: 
            node = ui_nodes.register_item[item_type]()
            node.load(item_dict)
            uuid = item_dict['uuid']
            items[uuid] = node
        
            inputs = node.get_all_inputs()
            print('inputs', inputs)
            for input_item in inputs:
                
                print(input_item.attribute.name)
                if input_item.attribute.name == 'eval':
                    print('here!!!!!!!!!!!')
                    eval_items[uuid] = node
                    break
            
            if not inputs:
                start_items[uuid] = node
            
        if item_dict['type'] == 4:
            connections.append(item_dict)
        
    
    for connection in connections:
        source_id = connection['source']
        target_id = connection['target']
        
        if target_id in items:
            if not target_id in in_connections:
                in_connections[target_id] = []
                
            in_connections[target_id].append(connection)
    
    print('eval items!!!')
    for uuid in eval_items:
        node = eval_items[uuid]
        node.run()
        
        visited[uuid] = None
    
    for uuid in start_items:
        node = start_items[uuid]
        node.run()
        
        visited[uuid] = None
        
    for uuid in in_connections:
        
        connections = in_connections[uuid]
        
        sources = []
        targets = []
        
        for connection in connections:
            source_id = connection['source']
            target_id = connection['target']
            
            sources.append(source_id)
            targets.append(target_id)
            
            if source_id in start_items:
                source_node = items[source_id]
                target_node = items[target_id]
                
                value = source_node.get_socket_value(connection['source name'])
                target_node.set_socket(connection['target name'], value)
                items[target_id]
            
            
        for source in sources:
            if source in visited:
                continue
            
            items[source].run()
            visited[source] = None
            
        for target in targets:
            if target in visited:
                continue
            
            items[target].run()
            visited[target] = None

def remove():
    rigs.remove_rigs()