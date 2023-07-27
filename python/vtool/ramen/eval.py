from .. import util, util_file
from .ui_lib import ui_nodes
from . import rigs 



def run(json_file):
    util.show('Run Eval')
    visited = {}
    in_connections = {}
    
    json_data = util_file.get_json(json_file)
    
    connections = []
    items = {}
    eval_items = {}
    start_items = {}
    
    util.show('Gathering Data')
    for item_dict in json_data:
        item_type = item_dict['type']
        if item_type in ui_nodes.register_item: 
            node = ui_nodes.register_item[item_type]()
            node.load(item_dict)
            uuid = item_dict['uuid']
            items[uuid] = node
        
            inputs = node.rig.get_ins()
            print('inputs', inputs)
            for input_name in inputs:
                
                if input_name == 'eval':
                    
                    eval_items[uuid] = node
                    break
            
            if not inputs:
                start_items[uuid] = node
            
        if item_dict['type'] == 4:
            connections.append(item_dict)
        
    
    for connection in connections:
        if not 'source' in connection:
            continue
        source_id = connection['source']
        target_id = connection['target']
        
        if target_id in items:
            if not target_id in in_connections:
                in_connections[target_id] = []
                
            in_connections[target_id].append(connection)
    
    util.show('Running Eval items')
    for uuid in eval_items:
        node = eval_items[uuid]
        node.run()
        
        visited[uuid] = None
        
        for connection in connections:
            if not 'source' in connection:
                continue
            source_id = connection['source']
            target_id = connection['target']
            
            if source_id == uuid:
            
                if target_id in items:
                    connected_node = items[target_id]
                    connected_node.run()
                    print(connected_node.name, connected_node.uuid)
                    
                    visited[connected_node.uuid] = None

    util.show('Running Start Items')
    for uuid in start_items:
        if uuid in visited:
            continue
        node = start_items[uuid]
        node.run()
        
        visited[uuid] = None

    util.show('Running Items')
    for uuid in items:
        if not uuid in in_connections:
            continue
        
        if uuid in visited:
            continue
        
        node = items[uuid]
        node.run()
        
        print(visited.keys())
        print(uuid)
        visited[uuid] = None

    util.show('Running Connections')
    for uuid in in_connections:
        
        connections = in_connections[uuid]
        
        sources = []
        targets = []
        
        for connection in connections:
            source_id = connection['source']
            target_id = connection['target']
            
            if not target_id in items:
                continue
            
            sources.append(source_id)
            targets.append(target_id)
            
            source_node = items[source_id]
            target_node = items[target_id]
            
            if not source_id in visited:
                source_node.run()
            
            value = source_node.get_socket_value(connection['source name'])
            print('test value', value)
            target_node.set_socket(connection['target name'], value)
            
        
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