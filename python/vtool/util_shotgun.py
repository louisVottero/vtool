from vtool import util_file
from vtool import util

sg = None

def get_sg():
    
    settings = util.get_env('VETALA_SETTINGS')
    
    global sg
    
    if settings and sg == None:
        
        settings_inst = util_file.SettingsFile()
        settings_inst.set_directory(settings)
        url = settings_inst.get('shotgun_url')
        name = settings_inst.get('shotgun_name')
        code = settings_inst.get('shotgun_code')
        
        
        api_path = settings_inst.get('shotgun_api')
        tank_path = settings_inst.get('shotgun_tank')
        util.add_to_PYTHONPATH(api_path)
        util.add_to_PYTHONPATH(tank_path)
        
        if util.has_shotgun_api():
            import shotgun_api3

        if url and name and code:
            sg = shotgun_api3.Shotgun(url,
                                      script_name=name,
                                      api_key=code)
        
        
    
    
    
        if sg != None:
            util.show('Using Shotgun')
    
    util.add_to_PYTHONPATH('D:/dev/git/python-api')
    import shotgun_api3
    sg = shotgun_api3.Shotgun('https://cryptidfx.shotgunstudio.com', script_name = 'Vetala', api_key = 'f976bb4f830b34f71605a9cdb0056c9e9968d5336932ad80e64b7ff7e0c95ec8')
    
    return sg

def get_projects():
    
    sg = get_sg()
    if not sg:
        return
    
    projects = sg.find('Project', [['sg_status','is','Active']], ['name'])
    
    return projects

def get_assets(project_name = None, asset_type = None):
    sg = get_sg()
    if not sg:
        return
    
    filters = []
    
    if project_name:
        filters.append(['project.Project.name', 'is', project_name])
    
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
def get_asset(project, sg_asset_type, name, step):
    
    settings = util.get_env('VETALA_SETTINGS')
    
    code = settings.get('shotgun_asset_path_code')
    
    code.replace('{project}', project)
    code.replace('{sg_asset_type}', sg_asset_type)
    code.replace('{asset_name}', name)
    code.replace('{step}', step)
    

"""
import tank
import sgtk



def login():
    
    from tank_vendor.shotgun_authentication import ShotgunAuthenticator
    cdm = sgtk.util.CoreDefaultsManager()
    authenticator = ShotgunAuthenticator(cdm)
    authenticator.clear_default_user()
    user = authenticator.get_user()
    sgtk.set_authenticated_user(user)

def get_file_info(filepath):
    
    tk = sgtk.sgtk_from_path(filepath)
    template = tk.template_from_path(filepath) #template
    fields = template.get_fields(filepath)
    
    return fields
"""
