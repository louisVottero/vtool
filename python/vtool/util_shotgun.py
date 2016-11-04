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
