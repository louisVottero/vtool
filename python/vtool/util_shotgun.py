from vtool import util_file
from vtool import util



sg = None
local_sgtk = None


def get_sg():
    
    if not util.has_shotgun_tank() and not util.has_shotgun_api():
        return
    
    global sg
    global local_sgtk
    
    settings = util.get_env('VETALA_SETTINGS')
    
    if settings and sg == None:
        
        
        settings_inst = util_file.SettingsFile()
        settings_inst.set_directory(settings)
        if not util.has_shotgun_tank():
            api_path = settings_inst.get('shotgun_api')
            util.add_to_PYTHONPATH(api_path)
        
        #url = settings_inst.get('shotgun_url')
        name = settings_inst.get('shotgun_name')
        code = settings_inst.get('shotgun_code')
        
        
        
        if util.has_shotgun_tank():
            
            import sgtk
            local_sgtk = sgtk
                
                
            try:
                from tank_vendor.shotgun_authentication import ShotgunAuthenticator
                cdm = sgtk.util.CoreDefaultsManager()    
                authenticator = ShotgunAuthenticator(cdm)
                user = authenticator.create_script_user(
                                                        api_script=name,
                                                        api_key=code
                                                        )
                
                sgtk.set_authenticated_user(user)
                
                sg = sgtk.Sgtk.shotgun.fget(1)
                
            except:
                
                try:
                    #for awesome town
                    from bsp.common.db import shotgun_access
                    sg = shotgun_access._getShotgunHandle(name, code)
                    util.show("Using bsp's shotgun_access to get the shotgun handle")
                    #end of for awesome town
                except:
                    util.error('Could not get shotgun api.  Check that your shotgun api script and key code are correct. \nShotgun toolkit might not be installed correctly. \nShotgun may have been initialized to a different project.')
        
        if sg == None:
            
            script_url = settings_inst.get('shotgun_url')
            
            try:
                import shotgun_api3
            except:
                util.warning('Could not access shotgun_api3')
            try:
                sg = shotgun_api3.Shotgun(script_url, name, code)
            except:
                util.warning('Could not access shotgun ui using, %s, %s, %s' % (script_url, name, code))
            
        if sg != None:
            util.show('Using Shotgun with name: %s and authentication key: %s' % (name, code))
    
    return sg

def get_projects():
    
    sg = get_sg()
    if not sg:
        return
    
    projects = sg.find('Project', [['sg_status','is','Active']], ['name'])
    
    return projects

def get_project_tank_name(name):
    
    project_name = name
    
    sg = get_sg()
    if not sg:
        return
    
    result = sg.find('Project', [['name', 'is', name]],['tank_name'])
    
    if result[0].has_key('tank_name'):
        return result[0]['tank_name']
    
    return project_name
    
    

def get_project_tank(project_name):
    sg = get_sg()
    
    if not sg:
        return
    
    entity = sg.find_one('Project', [['name', 'is',project_name]])
    
    global local_sgtk
    
    if entity:
        
        tank = None
        
        try:
            tank = local_sgtk.sgtk_from_entity('Project', entity['id'])
        except:
            if not util.is_in_maya():
                util.warning('Could not get path for project "%s" using sgtk.sgtk_from_entity. \n Shotgun may have been initialized to a different project.' % project_name)
            if util.is_in_maya():
                util.warning('Could not get path for project %s. Maya was probably loaded with a different project through Shotgun Desktop.' % project_name)
        
        return tank

def get_assets(project_name = None, asset_type = None):
    sg = get_sg()
    if not sg:
        return
    
    filters = []
    
    if project_name:
        filters.append(['project.Project.name', 'is', project_name])
    if asset_type:
        filters.append(['sg_asset_type', 'is', asset_type])
    
    assets = sg.find('Asset', filters, ['code', 'sg_asset_type'])
    
    return assets

def get_asset_steps():
    sg = get_sg()
    if not sg:
        return
    
    filters = []
    
    filters.append(['entity_type', 'is', 'Asset'])
    steps = sg.find('Step', filters, fields = ['code','short_name'])
    
    return steps

def get_asset_tasks(project_name, asset_step,asset_type,asset_name):
    
    sg = get_sg()
    if not sg:
        return
    
    filters = []
    
    asset = get_asset(project_name, asset_type,asset_name)
    
    filters.append(['entity', 'is', asset])
    filters.append(['step.Step.code', 'is', asset_step])
    
    if project_name:
        filters.append(['project.Project.name', 'is', project_name])
    
    
    
    """
    fields = [
    'content',
    'start_date',
    'due_date',
    'upstream_tasks',
    'downstream_tasks',
    'dependency_violation',
    'pinned'
    ]
    """
    
    tasks = sg.find('Task', filters, fields = ['content'])
    
    return tasks

def get_asset_step(name):
    
    sg = get_sg()
    if not sg:
        return
    
    filters = []
    
    filters.append(['entity_type', 'is', 'Asset'])
    filters.append(['code', 'is', name])
    
    steps = sg.find_one('Step', filters, fields = ['code','short_name'])
    
    return steps


def get_asset(project_name, sg_asset_type, name):
    
    sg = get_sg()
    if not sg:
        return
    
    filters = []
    filters.append(['project.Project.name', 'is', project_name])
    filters.append(['sg_asset_type', 'is', sg_asset_type])
    filters.append(['code', 'is', name])
    
    asset = sg.find_one('Asset', filters)
    return asset
    
def get_template(project, publish_path = False):
    tank = get_project_tank(project)
    
    if not tank:
        return
    
    settings = util.get_env('VETALA_SETTINGS')
    
    settings_inst = util_file.SettingsFile()
    settings_inst.set_directory(settings)
    
    if publish_path:
        code = settings_inst.get('shotgun_asset_publish_template')
    if not publish_path:
        code = settings_inst.get('shotgun_asset_work_template')
    
    publish_template =  tank.templates[code]
    
    return publish_template
    
    
    
def get_asset_path(project, sg_asset_type, name, step, publish_path = False, task = None, custom = None, asset_is_name = False):
    
    publish_template = get_template(project, publish_path)
    
    step_entity = get_asset_step(step)
    
    fields = {}
    fields['sg_asset_type'] = sg_asset_type
    fields['Asset'] = name
    fields['Step'] = step_entity['short_name']
    if task:
        fields['Task'] = task
    if custom:
        fields['name'] = custom
    if asset_is_name:
        fields['name'] = name
        
    fields['version'] = 1
    
    publish_path = publish_template.apply_fields(fields)
    
    publish_dir = util_file.get_dirname(publish_path)
    
    if not util_file.is_dir(publish_dir):
        fields['Step'] = step_entity['code']
        publish_path = publish_template.apply_fields(fields)
    
    return publish_path

def get_latest_file(project, sg_asset_type, name, step, publish_path = False, task = None, custom = None, asset_is_name = False):
    
    step_entity = get_asset_step(step)
    
    fields = {}
    fields['sg_asset_type'] = sg_asset_type
    fields['Asset'] = name
    if step_entity.has_key('short_name'):
        fields['Step'] = step_entity['short_name']
    if task:
        fields['Task'] = task
    if custom:
        fields['name'] = custom
    if asset_is_name:
        fields['name'] = name
    fields['version'] = 1
    
    publish_template = get_template(project, publish_path)
    
    if not publish_template:
        return
    
    publish_path = publish_template.apply_fields(fields)
    
    start_path = publish_path
    
    publish_path = util_file.get_dirname(publish_path)
    
    files = util_file.get_files_date_sorted(publish_path)
    
    files.reverse()
    
    
    for filename in files:
        
        test_path = util_file.join_path(publish_path, filename)
        
        dict_value = publish_template.validate_and_get_fields(test_path)
        
        if dict_value:
            return test_path
        
    return start_path

def get_next_file(project, sg_asset_type, name, step, publish_path = False, task = None, custom = None, asset_is_name = False):

    step_entity = get_asset_step(step)
    
    fields = {}
    fields['sg_asset_type'] = sg_asset_type
    fields['Asset'] = name
    if step_entity.has_key('short_name'):
        fields['Step'] = step_entity['short_name']
    if task:
        fields['Task'] = task
    if custom:
        fields['name'] = custom
    if asset_is_name:
        fields['name'] = name
    fields['version'] = 1
    
    publish_template = get_template(project, publish_path)
    
    if not publish_template:
        return
    
    publish_path = publish_template.apply_fields(fields)
    
    start_path = publish_path
    
    publish_path = util_file.get_dirname(publish_path)
    
    files = util_file.get_files_date_sorted(publish_path)
    
    files.reverse()
    
    for filename in files:
        
        test_path = util_file.join_path(publish_path, filename)
        
        dict_value = publish_template.validate_and_get_fields(test_path)
        
        if dict_value:
            dict_value['version'] = dict_value['version'] + 1
            
            path = publish_template.apply_fields(dict_value)
            return path
    
    return start_path