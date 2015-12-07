# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import traceback
import threading

import util       
import util_file

if util.is_in_maya():
    import maya.cmds as cmds
    import maya.mel as mel
    
import maya_lib.core
import maya_lib.attr
import maya_lib.deform
import maya_lib.anim
import maya_lib.curve
import maya_lib.corrective
import maya_lib.rigs_util

class DataManager(object):
    
    def __init__(self):
        self.available_data = [MayaAsciiFileData(), 
                               MayaBinaryFileData(), 
                               ScriptManifestData(),
                               ScriptPythonData(),
                               ControlCvData(),
                               SkinWeightData(),
                               DeformerWeightData(),
                               AnimationData(),
                               ControlAnimationData(),
                               #AtomData(),
                               MayaShadersData(),
                               MayaAttributeData(),
                               PoseData()]
        
    def get_available_types(self):
        
        types = []
        
        for data in self.available_data:          
            types.append( data.get_type() )
    
        return types
                
    def get_type_instance(self, data_type):
        
        for data in self.available_data:
            
            if data.is_type_match(data_type):
                return data
            
class DataFolder(util_file.FileManager):
    
    def __init__(self, name, filepath):
        super(DataFolder, self).__init__(filepath)
        
        self.name = name
        self.data_type = None
        self.filepath = filepath
        
        test_path = util_file.join_path(filepath, name)
        
        is_folder = util_file.is_dir(test_path)
        
        if is_folder:
            self.folder_path = test_path
        
        if not is_folder:
            self._create_folder()
        
        self.settings = None
        
    def _load_folder(self):
        self._set_default_settings()
        
    def _set_settings_path(self, folder):
        if not self.settings:
            self._load_folder()
        
        self.settings.set_directory(folder, 'data.type')
        
    def _set_default_settings(self):
        
        self.settings = util_file.SettingsFile()
        self._set_settings_path(self.folder_path)
        
        self.settings.set('name', str(self.name))
        data_type = self.settings.get('data_type')
        self.settings.set('data_type', str(data_type))
        self.data_type = data_type
        
    def _create_folder(self):
        path = util_file.create_dir(self.name, self.filepath)
        self.folder_path = path
        
        self._set_default_settings()
    
    def _set_name(self, name):
        if not self.settings:
            self._load_folder()
        
        self.name = name
        self.settings.set('name', str(self.name))
        
                
    def get_data_type(self):
        if not self.settings:
            self._load_folder()
        
        return self.settings.get('data_type')
    
    def set_data_type(self, data_type):
        
        if not self.settings:
            self._load_folder()

        self.data_type = data_type
        self.settings.set('data_type', str(data_type))
        
    def get_folder_data_instance(self):
        
        if not self.settings:
            self._load_folder()
        
        if not self.name:
            return
        
        data_type = self.settings.get('data_type')
        if not data_type:
            data_type = self.data_type
        
        if not data_type:
            return
        
        data_manager = DataManager()
        instance = data_manager.get_type_instance(data_type)
        
        if instance:
            instance.set_directory(self.folder_path)
            instance.set_name(self.name)
        
        return instance
    
    def rename(self, new_name):
        
        instance = self.get_folder_data_instance()
        instance.rename(new_name)
        
        folder = util_file.rename(self.folder_path, new_name)
        
        if not folder:
            return
        
        self.folder_path = folder
        self._set_settings_path(folder)
        self._set_name(new_name)
        
        return self.folder_path
    
    def delete(self):
        
        name = util_file.get_basename(self.folder_path)
        directory = util_file.get_dirname(self.folder_path)
        
        util_file.delete_dir(name, directory)
    
class DataFile(util_file.FileManager):
    
    def __init__(self, name, directory):
        
        self.filepath = util_file.create_file(name, directory)
        
        self.name = util_file.get_basename(self.filepath)
        self.directory = util_file.get_dirname(self.filepath)
        
        super(DataFile, self).__init__(self.filepath)
        
    def _get_folder(self):
        
        name = util_file.get_basename_no_extension(self.name)
        
        dirpath = util_file.join_path(self.directory, name)

        return dirpath
        
    def _create_folder(self):
        
        name = util_file.get_basename_no_extension(self.name)
        
        folder = util_file.create_dir(name, self.directory)
        return folder
    
    def _rename_folder(self, new_name):
        
        dirpath = self._get_folder()
        
        
        if not util_file.is_dir(dirpath):
            return
        
        new_name = util_file.get_basename_no_extension(new_name)
        
        if util_file.is_dir(dirpath):
            util_file.rename(dirpath, new_name)
        
    def _create_version_folder(self):
        
        self.version_path = util_file.create_dir('.versions', self.directory)
        
    def version_file(self, comment):
        
        self._create_version_folder()
        version_file = util_file.VersionFile(self.filepath)
        version_file.set_version_folder(self.version_path)
        version_file.set_version_folder_name('.%s' % self.name)
        version_file.set_version_name(self.name)
        version_file.save(comment)
        
    def add_child(self, filepath):
        
        folder = self._create_folder()
        
        child_name = util_file.get_basename(filepath)
        new_child_path = util_file.join_path(folder, child_name)
        
        util_file.move(filepath, new_child_path)
        
        path_name = util_file.join_path(self.name, child_name)
        
        return self.directory, path_name
        
    def delete(self):
        
        folder = self._get_folder()
        
        if folder:
            util_file.delete_dir(self.name, self.directory)
            
        if util_file.is_file(self.filepath):
            util_file.delete_file(self.name, self.directory)
    
    def rename(self, new_name):
        
        filepath = util_file.rename(self.filepath, new_name)
        
        if not filepath:
            return
        
        self._rename_folder(new_name)
        
        self.name = new_name
        self.directory = util_file.get_dirname(filepath)
        self.filepath = filepath
        
        return self.filepath
    
class Data(object):
    def __init__(self, name = None):
        self.data_type = self._data_type()
        self.data_extension = self._data_extension()
        
        self.name = name
        
        if not name:
            self.name = self._data_name()
              
    def _data_name(self):
        return 'data'
                 
    def _data_type(self):
        return None
    
    def set_name(self, name):
        self.name = name
    
    def is_type_match(self, data_type):
        
        if data_type == self.data_type:
            return True
        
        return False
    
    def get_type(self):
        return self.data_type
    

    
class FileData(Data):
    
    def __init__(self, name = None):
        super(FileData, self).__init__(name)
        
        self.directory = None
        
        self.settings = util_file.SettingsFile()
        self.file = None
        
    def _data_extension(self):
        return 'data'
        
    def _get_file_name(self):
        
        if self.data_extension:
            return '%s.%s' % (self.name, self.data_extension)
        if not self.data_extension:
            return self.name
           
    def set_directory(self, directory):
        self.directory = directory
        self.settings.set_directory(self.directory, 'data.type')
        self.name = self.settings.get('name')
        
    def create(self):
        name = self.name
        
        self.file = util_file.create_file('%s.%s' % (name, self.data_extension), self.directory)    
    
    def get_file(self):
        
        filepath = util_file.join_path(self.directory, self._get_file_name())
        
        if util_file.is_file(filepath):
            return filepath
        
        if util_file.is_dir(filepath):
            return filepath
        
    def rename(self, new_name):
        
        old_name = self.name
        
        old_filepath = util_file.join_path(self.directory, '%s.%s' % (old_name, self.data_extension))
        
        self.set_name(new_name)
        
        found = False
        
        if util_file.is_file(old_filepath):
            found = True
            
        
        if util_file.is_dir(old_filepath):
            found = True
    
        if found:
        
            util_file.rename(old_filepath, self._get_file_name())
        
            return self._get_file_name()
    
class ScriptData(FileData):
    
    def save(self, lines, comment = None):
        
        filepath = util_file.join_path(self.directory, self._get_file_name())
        
        write_file = util_file.WriteFile(filepath)
        write_file.write(lines, last_line_empty = False)
        
        version = util_file.VersionFile(filepath)
        version.save(comment)
        
    def set_lines(self, lines):
        self.lines = lines
        
    def create(self):
        super(ScriptData, self).create()
        
        filename = self.get_file()
        
        if not hasattr(self, 'lines'):
            return
        
        if self.lines and filename:
            
            write = util_file.WriteFile(filename)
            write.write(self.lines)
    
class ScriptManifestData(ScriptData):
    
    def _data_type(self):
        return 'script.manifest'
    
class ScriptPythonData(ScriptData):

    def _data_type(self):
        return 'script.python'
    
    def _data_extension(self):
        return 'py'
        
    def open(self):
        lines = ''
        return lines

class ScriptMelData(ScriptData):

    def _data_type(self):
        return 'script.mel'
    
    def _data_extension(self):
        return 'mel'
   
class CustomData(FileData):
    
    def import_data(self):
        pass
    
    def export_data(self):
        pass
      
class MayaCustomData(CustomData):
    def _center_view(self):
        try:
            cmds.select(cl = True)
            cmds.viewFit(an = True)
            self._fix_camera()
        except:
            util.show('Could not center view')
            
    def _fix_camera(self):
        
        camera_pos = cmds.xform('persp', q = True, ws = True, t = True)
        
        distance = util.get_distance([0,0,0], camera_pos)
        distance = (distance*2)
        
        cmds.setAttr('persp.farClipPlane', distance)
        
        if distance > 10000:
            cmds.setAttr('persp.nearClipPlane', distance/50,000)
        
        if distance > 1000000:
            cmds.setAttr('persp.nearClipPlane', 100)
            
class ControlCvData(MayaCustomData):
    """
    maya.control_cvs
    Exports/Imports cv positions on controls.
    All control cvs will be exported regardless of selection.
    All control cvs will be imported regardless of selection.
    """
    
    def _data_name(self):
        return 'control_cvs'
        
    def _data_type(self):
        return 'maya.control_cvs'
    
    def import_data(self, filename = None):
        
        if not filename:
            directory = self.directory
            name = self.name
        
        if filename:
            directory = util_file.get_dirname(filename)
            name = util_file.get_basename(filename)
        
        controls = maya_lib.rigs_util.get_controls()
        
        library = maya_lib.curve.CurveDataInfo()
        library.set_directory(directory)
        if filename:
            library.set_active_library(name, skip_extension= True)
        if not filename:
            library.set_active_library(name)
            
        for control in controls:
            
            shapes = maya_lib.core.get_shapes(control)
            
            if not shapes:
                continue
            
            library.set_shape_to_curve(control, control, True)
             
        self._center_view()
        
        util.show('Imported %s data.' % self.name)
    
    def export_data(self, comment):
        
        library = maya_lib.curve.CurveDataInfo()
        controls = maya_lib.rigs_util.get_controls()
        
        library.set_directory(self.directory)
        library.set_active_library(self.name)
        
        for control in controls:
            
            library.add_curve(control)
            
        filepath = library.write_data_to_file()
        
        version = util_file.VersionFile(filepath)
        version.save(comment)
        
        util.show('Exported %s data.' % self.name)
          
class SkinWeightData(MayaCustomData):
    """
        maya.skin_weights
        Export skin cluster weights on selected geo.
        Import available skin cluster weights for geo, or only the weights on selected geo.
    """
    def _data_name(self):
        return 'skin_weights'

    def _data_extension(self):
        return ''
    
    def _data_type(self):
        return 'maya.skin_weights'
        
    def _get_influences(self, folder_path):
          
        files = util_file.get_files(folder_path)
        
        info_file = util_file.join_path(folder_path, 'influence.info')
        info_lines = util_file.get_file_lines(info_file)
        
        influence_dict = {}
        
        for line in info_lines:
            if not line:
                continue
            
            line_dict = eval(line)
            influence_dict.update(line_dict)
        
        for influence in files:
            if influence == 'influence.info':
                continue
            
            read_thread = ReadWeightFileThread() 
            
            try:
                influence_dict = read_thread.run(influence_dict, folder_path, influence)
            except:
                util.show(traceback.format_exc())
                util.show('Errors with %s weight file.' % influence)
                    
        return influence_dict
    
    def _test_shape(self, mesh, shape_types):
        
        for shape_type in shape_types:
            
            if maya_lib.core.has_shape_of_type(mesh, shape_type):
                
                return True
        
        return False
        
    def _import_maya_data(self, filepath = None):
        
        if not filepath:
            path = util_file.join_path(self.directory, self.name)
        if filepath:
            path = filepath
        
        selection = cmds.ls(sl = True)
        
        if selection:
            folders = selection
            
        if not selection:
            folders = util_file.get_folders(path)
        
        if not folders:
            util.warning('No mesh folders found in skin data.')
            return
        
        for folder in folders:
            
            util.show('Importing weights on %s' % folder)
            
            mesh = folder
            
            if not cmds.objExists(mesh):
                util.warning('Skipping %s. It does not exist.' % mesh)
                continue
            
            shape_types = ['mesh','nurbsSurface', 'nurbsCurve', 'lattice']
            shape_is_good = self._test_shape(mesh, shape_types)
            
            if not shape_is_good:
                cmds.warning('%s does not have a supported shape node. Currently supported nodes include: %s.' % (mesh, shape_types))
                continue
            
            skin_cluster = maya_lib.deform.find_deformer_by_type(mesh, 'skinCluster')
            
            folder_path = util_file.join_path(path, folder)
            
            if not util_file.is_dir(folder_path):
                continue
            
            influence_dict = self._get_influences(folder_path)

            influences = influence_dict.keys()
            
            if not influences:
                continue
            
            influences.sort()
            
            for influence in influences:
                if not cmds.objExists(influence):
                    cmds.select(cl = True)
                    cmds.joint( n = influence, p = influence_dict[influence]['position'] )
            
            if not skin_cluster:
                skin_cluster = cmds.skinCluster(influences, mesh,  tsb = True, n = 'skin_%s' % mesh)[0]
            
            cmds.setAttr('%s.normalizeWeights' % skin_cluster, 0)
            
            maya_lib.deform.set_skin_weights_to_zero(skin_cluster)
            
            influence_inc = 0
              
            influence_index_dict = maya_lib.deform.get_skin_influences(skin_cluster, return_dict = True)
            
            progress_ui = maya_lib.core.ProgressBar('import skin', len(influence_dict.keys()))
            
            for influence in influences:
                
                progress_ui.status('importing skin mesh: %s,  influence: %s' % (mesh, influence))
                    
                weights = influence_dict[influence]['weights']
                
                if not influence in influence_index_dict:
                    continue
                
                index = influence_index_dict[influence]
                
                for inc in range(0, len(weights)):
                            
                    weight = float(weights[inc])
                    
                    if weight == 0 or weight < 0.0001:
                        continue
                    
                    cmds.setAttr('%s.weightList[%s].weights[%s]' % (skin_cluster, inc, index), weight)
                                    
                progress_ui.inc()
                
                if progress_ui.break_signaled():
                    break
                
                influence_inc += 1
            
            progress_ui.end()                    
            
            cmds.skinCluster(skin_cluster, edit = True, normalizeWeights = 1)
            cmds.skinCluster(skin_cluster, edit = True, forceNormalizeWeights = True)
        
            file_path = util_file.join_path(folder_path, 'settings.info')
            
            if util_file.is_file(file_path):
            
                lines = util_file.get_file_lines(file_path)
                for line in lines:
                    
                    test_line = line.strip()
                    
                    if not test_line:
                        continue
                    
                    line_list = eval(line)
            
                    attr_name = line_list[0]
                    value = line_list[1]
            
                    if attr_name == 'blendWeights':
                        
                        maya_lib.deform.set_skin_blend_weights(skin_cluster, value)
                    
                    if attr_name == 'skinningMethod':
                        
                        cmds.setAttr('%s.skinningMethod' % skin_cluster, value)

        util.show('Imported %s data' % self.name)
                
        self._center_view()
        
    def import_data(self, filepath = None):
       
        if util.is_in_maya():
            
            cmds.undoInfo(state = False)
            
            self._import_maya_data(filepath)
                         
            cmds.undoInfo(state = True)               
      
    def export_data(self, comment):
        
        path = util_file.join_path(self.directory, self.name)
        
        selection = cmds.ls(sl = True)
        
        for thing in selection:
            
            util.show('Exporting weights on %s' % thing)
            
            split_thing = thing.split('|')
            
            if len(split_thing) > 1:
                util.warning('Skin export failed. There is more than one %s.' % maya_lib.core.get_basename(thing))
                continue
            
            skin = maya_lib.deform.find_deformer_by_type(thing, 'skinCluster')
            
            if not skin:
                util.warning('Skin export failed. No skinCluster found on %s.' % thing)
            
            if skin:
                
                geo_path = util_file.join_path(path, thing)
                
                if util_file.is_dir(geo_path):
                    util_file.delete_dir(thing, path)
                
                geo_path = util_file.create_dir(thing, path)
                
                weights = maya_lib.deform.get_skin_weights(skin)
                                
                info_file = util_file.create_file( 'influence.info', geo_path )
                
                
                info_lines = []
                
                for influence in weights:
                    
                    if influence == None or influence == 'None':
                        continue
                    
                    weight_list = weights[influence]
                    
                    if not weight_list:
                        continue
                    
                    thread = LoadWeightFileThread()
                    
                
                    #util_file.ReadFile(geo_path)
                    
                    influence_line = thread.run(influence, skin, weights[influence], geo_path)
                    
                    if influence_line:
                        info_lines.append(influence_line)
                
                write_info = util_file.WriteFile(info_file)
                write_info.write(info_lines)        
                
                settings_file = util_file.create_file('settings.info', geo_path)
                
                blend_weights_attr = '%s.blendWeights' % skin
                skin_method_attr = '%s.skinningMethod' % skin
                
                settings_lines = []
                
                if cmds.objExists(blend_weights_attr):
                    blend_weights = maya_lib.deform.get_skin_blend_weights(skin)
                    
                    write = util_file.WriteFile(settings_file)
                    settings_lines.append("['blendWeights', %s]" % blend_weights)
                    
                
                if cmds.objExists(skin_method_attr):
                    
                    skin_method = cmds.getAttr(skin_method_attr)
                    
                    
                    settings_lines.append("['skinningMethod', %s]" % skin_method)
                
                write_settings = util_file.WriteFile(settings_file)
                write_settings.write(settings_lines)
                
        
        version = util_file.VersionFile(path)
        version.save(comment)
        
             
class LoadWeightFileThread(threading.Thread):
    def __init__(self):
        super(LoadWeightFileThread, self).__init__()
        
    def run(self, influence_index, skin, weights, path):
        
        influence_name = maya_lib.deform.get_skin_influence_at_index(influence_index, skin)
        
        if not influence_name or not cmds.objExists(influence_name):
            return
        
        filepath = util_file.create_file('%s.weights' % influence_name, path)
        
        if not util_file.is_file(filepath):
            util.show('%s is not a valid path.' % filepath)
            return
        
        write = util_file.WriteFile(filepath)
        write.write_line(weights)     
        
        influence_position = cmds.xform(influence_name, q = True, ws = True, t = True)
        return "{'%s' : {'position' : %s}}" % (influence_name, str(influence_position))
        
class ReadWeightFileThread(threading.Thread):
    def __init__(self):
        super(ReadWeightFileThread, self).__init__()
        
    def run(self, influence_dict, folder_path, influence):
        file_path = util_file.join_path(folder_path, influence)
        
        influence = influence.split('.')[0]
        
        lines = util_file.get_file_lines(file_path)
        weights = eval(lines[0])
        
        if influence in influence_dict:
            influence_dict[influence]['weights'] = weights
        
        return influence_dict
    
class BlendshapeWeightData(MayaCustomData):
    
    def _data_name(self):
        return 'blendshape_weights'

    def _data_extension(self):
        return ''
    
    def _data_type(self):
        return 'maya.blendshape_weights'
    
class DeformerWeightData(MayaCustomData):
    """
    maya.deform_weights
    Export/Import weights of clusters and wire deformers.
    Will not work if cluster or wire deformer is affecting more than one piece of geo.
    """
    def _data_name(self):
        return 'deform_weights'

    def _data_extension(self):
        return ''
    
    def _data_type(self):
        return 'maya.deform_weights'
    
    def export_data(self, comment = None):
        
        
        path = util_file.join_path(self.directory, self.name)
        
        util_file.create_dir(self.name, self.directory)
        
        
        meshes = maya_lib.geo.get_selected_meshes()
        
        for mesh in meshes:
            
            clusters = maya_lib.deform.find_deformer_by_type(mesh, 'cluster', return_all = True)
            wires = maya_lib.deform.find_deformer_by_type(mesh, 'wire', return_all = True)
            
            if not clusters:
                clusters = []
            if not wires:
                wires = []
            
            deformers = clusters + wires
            
            if not deformers:
                util.warning('Did not find a cluster or wire deformer on %s.' % mesh)
                continue
            
            for deformer in deformers:
                
                weights = maya_lib.deform.get_deformer_weights(deformer)
                
                filepath = util_file.create_file('%s.weights' % deformer, path)
                
                if not filepath:
                    return
                
                write_info = util_file.WriteFile(filepath)
                
                info_lines = [weights]
                
                write_info.write(info_lines)
    
        util.show('Exported %s data' % self.name)
    
    def import_data(self):
        
        path = util_file.join_path(self.directory, self.name)
        
        files = util_file.get_files(path)
        
        for filename in files:
            
            file_path = util_file.join_path(path, filename)
            
            lines = util_file.get_file_lines(file_path)
            
            if lines:
                weights = eval(lines[0])
                
            if not lines:
                return
            
            deformer = filename.split('.')[0]
            
            if cmds.objExists(deformer):
                maya_lib.deform.set_deformer_weights(weights, deformer)
                
            if not cmds.objExists(deformer):
                util.warning('Import failed: Deformer %s does not exist.' % deformer)    
                 
        util.show('Imported %s data' % self.name)
        
class MayaShadersData(CustomData):
    """
    maya.shaders
    Export/Import shaders.
    This only works for maya shaders. Eg. Blinn, Lambert, etc.
    """
    maya_ascii = 'mayaAscii'
    
    def _data_type(self):
        return 'maya.shaders'
    
    def _data_name(self):
        return 'shaders'
    
    def _data_extension(self):
        return ''
    
    def import_data(self):
        
        path = util_file.join_path(self.directory, self.name)
        
        files = util_file.get_files_with_extension('ma', path)
            
        info_file = util_file.join_path(path, 'shader.info')
        info_lines = util_file.get_file_lines(info_file)
        
        info_dict = {}
        
        for line in info_lines:
            if not line:
                continue
            
            shader_dict = eval(line)
                
            for key in shader_dict:
                info_dict[key] = shader_dict[key]
        
        for filename in files:

            filepath = util_file.join_path(path, filename)
            
            name = filename.split('.')[0]
            
            cmds.file(filepath, f = True, i = True, iv = True)
            
            if not name in info_dict:
                continue
            
            meshes = info_dict[name]
            
            if not meshes:
                continue
            
            for mesh in meshes:
                if not cmds.objExists(mesh):
                    continue
                
                cmds.sets( mesh, e = True, forceElement = name)
    
    def export_data(self, comment):
        
        shaders = cmds.ls(type = 'shadingEngine')
        
        path = util_file.join_path(self.directory, self.name)
        
        util_file.refresh_dir(path)
        
        info_file = util_file.create_file( 'shader.info', path )
        
        write_info = util_file.WriteFile(info_file)
        
        info_lines = []
        
        skip_shaders = ['initialParticleSE', 'initialShadingGroup']
        
        for shader in shaders:

            if shader in skip_shaders:
                continue
            
            members = cmds.sets(shader, q = True)
            info_lines.append("{'%s' : %s}" % (shader, members))
            
            
            filepath = util_file.join_path(path, '%s.ma' % shader)
        
            if util_file.is_file(filepath):
                util_file.delete_file(util_file.get_basename(filepath), path)
        
            cmds.file(rename = filepath)
            
            cmds.select(shader, noExpand = True)
            
            selection = cmds.ls(sl = True)
            
            if selection:            
                cmds.file(exportSelected = True, 
                          prompt = False, 
                          force = True, 
                          pr = True, 
                          type = self.maya_ascii)
        
        write_info.write(info_lines)
            
        version = util_file.VersionFile(path)
        version.save(comment)    
        
class AnimationData(MayaCustomData):
    """
    maya.animation
    Export/Import all the keyframes in a scene with their connection info. 
    Will export/import blendWeighted as well.
    """
    def _data_name(self):
        return 'animation'
    
    def _data_type(self):
        return 'maya.animation'
    
    def _get_keyframes(self):
        keyframes = cmds.ls(type = 'animCurve')
        return keyframes

    def _get_blend_weighted(self):
        blend_weighted = cmds.ls(type = 'blendWeighted')
        return blend_weighted
    
    def export_data(self, comment):
        
        keyframes = self._get_keyframes()
        blend_weighted = self._get_blend_weighted()
        
        if not keyframes:
            return
        
        if blend_weighted:
            keyframes = keyframes + blend_weighted
        
        path = util_file.join_path(self.directory, 'keyframes')
        
        util_file.refresh_dir(path)
        
        info_file = util_file.create_file( 'animation.info', path )
        
        write_info = util_file.WriteFile(info_file)
        
        info_lines = []
        
        all_connections = []
        
        cmds.select(cl = True)
        
        for keyframe in keyframes:
            
            if not cmds.objExists(keyframe):
                continue
            
            inputs = []
            
            if not cmds.nodeType(keyframe) == 'blendWeighted':
                inputs = maya_lib.attr.get_attribute_input('%s.input' % keyframe)
                
            outputs = maya_lib.attr.get_attribute_outputs('%s.output' % keyframe)
                        
            if not inputs and not outputs:
                continue
                        
            cmds.select(keyframe, add = True)
            
            connections = maya_lib.attr.Connections(keyframe)
            connections.disconnect()
            
            all_connections.append(connections)
            
            info_lines.append("{'%s' : {'output': %s, 'input': '%s'}}" % (keyframe, outputs, inputs))
            
        filepath = util_file.join_path(path, 'keyframes.ma')
        cmds.file(rename = filepath)
            
        cmds.file( force = True, options = 'v=0;', typ = 'mayaAscii', es = True )
            
        for connection in all_connections:
            connection.connect()
            
        write_info.write(info_lines)
            
        version = util_file.VersionFile(path)
        version.save(comment)
        
        util.show('Exported %s data.' % self.name)
        
    def import_data(self):
        
        path = util_file.join_path(self.directory, 'keyframes')
        
        if not util_file.is_dir(path):
            return
        
        filepath = util_file.join_path(path, 'keyframes.ma')
        
        if not util_file.is_file(filepath):
            return
            
        info_file = util_file.join_path(path, 'animation.info')
        
        if not util_file.is_file(info_file):
            return
        
        info_lines = util_file.get_file_lines(info_file)
        
        if not info_lines:
            return
        
        info_dict = {}
        
        for line in info_lines:
            if not line:
                continue
            
            keyframe_dict = eval(line)
                
            for key in keyframe_dict:
                
                if cmds.objExists(key):
                    cmds.delete(key)
                    
                
                info_dict[key] = keyframe_dict[key]
        
        cmds.file(filepath, f = True, i = True, iv = True)
        
        for key in info_dict:
            keyframes = info_dict[key]
            
            outputs = keyframes['output']
            
            if outputs:
                for output in outputs:
                    if not cmds.objExists(output):
                        continue
                    
                    locked = cmds.getAttr(output, l = True)
                    if locked:
                        cmds.setAttr(output, l = False)
                    
                    try:
                        cmds.connectAttr('%s.output' % key, output)
                    except:
                        cmds.warning('\tCould not connect %s.output to %s' % (key,output))
                        
                    if locked:
                        cmds.setAttr(output, l = False)

            input_attr = keyframes['input']
            
            if input_attr:
                
                if not cmds.objExists(input_attr):
                    continue
                try:
                    cmds.connectAttr(input_attr, '%s.input' % key)
                except:
                    cmds.warning('\tCould not connect %s to %s.input' % (input_attr,key))
                    
        util.show('Imported %s data.' % self.name)

    
class ControlAnimationData(AnimationData):
    """
    maya.control_animation
    Only import/export keframes on controls.
    Good for saving out poses. 
    """
    def _data_name(self):
        return 'control_animation'
    
    def _data_type(self):
        return 'maya.control_animation'
    
    def _get_keyframes(self):
        
        controls = maya_lib.rigs_util.get_controls()
        
        keyframes = []
        
        
        for control in controls:
            
            sub_keyframes = maya_lib.anim.get_input_keyframes(control, node_only = True)
            if sub_keyframes:
                keyframes += sub_keyframes
        
        return keyframes

    def _get_blend_weighted(self):
        
        return None
        
class AtomData(MayaCustomData):
    """
    Not in use.
    """
    def _data_name(self):
        return 'animation'

    def _data_extension(self):
        return 'atom'
    
    def _data_type(self):
        return 'maya.atom'
    
    def export_data(self, comment):
        nodes = cmds.ls(type = 'transform')
        cmds.select(nodes)
        
        file_name = '%s.%s' % (self.name, self.data_extension)
        file_path = util_file.join_path(self.directory, file_name)
        
        options = 'precision=8;statics=0;baked=1;sdk=1;constraint=0;animLayers=1;selected=selectedOnly;whichRange=1;range=1:10;hierarchy=none;controlPoints=0;useChannelBox=1;options=keys;copyKeyCmd=-animation objects -option keys -hierarchy none -controlPoints 0'
        
        if not cmds.pluginInfo('atomImportExport', query = True, loaded = True):
            cmds.loadPlugin('atomImportExport.mll')
        
        mel.eval('vtool -force -options "%s" -typ "atomExport" -es "%s"' % (options, file_path))
        
        version = util_file.VersionFile(file_path)
        version.save(comment)
        
    def import_data(self):
        
        nodes = cmds.ls(type = 'transform')
        cmds.select(nodes)
        
        file_name = '%s.%s' % (self.name, self.data_extension)
        file_path = util_file.join_path(self.directory, file_name)  

        if not cmds.pluginInfo('atomImportExport', query = True, loaded = True):
            cmds.loadPlugin('atomImportExport.mll')
        
        options = ';;targetTime=3;option=insert;match=hierarchy;;selected=selectedOnly;search=;replace=;prefix=;suffix=;'
        
        mel.eval('vtool -import -type "atomImport" -ra true -namespace "test" -options "%s" "%s"' % (options, file_path))
        
        self._center_view()      
        
class PoseData(MayaCustomData):
    """
    maya.pose
    Export/Import pose correctives.
    """
    maya_binary = 'mayaBinary'
    maya_ascii = 'mayaAscii'

    def _data_name(self):
        return 'pose'

    def _data_extension(self):
        return ''
    
    def _data_type(self):
        return 'maya.pose' 

    def _save_file(self, filepath):
        cmds.file(rename = filepath)
        #ch     chn     con     exp     sh
        cmds.file(exportSelected = True, prompt = False, force = True, pr = True, ch = False, chn = True, exp = True, con = False, sh = False, stx = 'never', typ = self.maya_ascii)
        
    def _import_file(self, filepath):
        
        if util_file.is_file(filepath):
            cmds.file(filepath, f = True, i = True, iv = True, shd = 'shadingNetworks')
        
        if not util_file.is_file(filepath):
            mel.eval('warning "File does not exist"')

    def _filter_inputs(self, inputs):
        
        for node in inputs:
            if not cmds.objExists(node):
                continue
            
            if cmds.nodeType(node) == 'hyperLayout':
                cmds.delete(node)
                
    def _get_inputs(self, pose):
        
        if not pose:
            return []
        
        sub_inputs = self._get_sub_inputs(pose)
        
        inputs = maya_lib.attr.get_inputs(pose)
        outputs = maya_lib.attr.get_outputs(pose)

        if inputs:
            inputs.append(pose)

        if not inputs:
            inputs = [pose]
        
        if outputs:
            inputs = inputs + outputs                              
        
        if sub_inputs:
            
            inputs = inputs + sub_inputs
        
        return inputs
  
    def _get_sub_inputs(self, pose):
        
        manager = maya_lib.corrective.PoseManager()
        manager.set_pose_group(pose)
        
        sub_poses = manager.get_poses()
        inputs = []
        
        if sub_poses:
            sub_inputs = []
            for sub_pose in sub_poses:
        
                sub_inputs = self._get_inputs(sub_pose)
                inputs = inputs + sub_inputs
        
        return inputs
  
    def _select_inputs(self, pose):
        
        inputs = self._get_inputs(pose)
        
        cmds.select(cl = True)
        cmds.select(inputs, ne = True)
        
        return inputs
            
    def export_data(self, comment):
        unknown = cmds.ls(type = 'unknown')
        
        if unknown:
            
            value = cmds.confirmDialog( title='Unknown Nodes!', message= 'Unknown nodes usually happen when a plugin that was being used is not loaded.\nLoad the missing plugin, and the unknown nodes could become valid.\n\nDelete unknown nodes?\n', 
                                    button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
        
            if value == 'Yes':
                maya_lib.core.delete_unknown_nodes()
        
        dirpath = util_file.join_path(self.directory, self.name)
        
        if util_file.is_dir(dirpath):
            name = util_file.get_basename(dirpath)
            dirname = util_file.get_dirname(dirpath)
            util_file.delete_dir(name, dirname)
        
        
        dir_path = util_file.create_dir(self.name, self.directory)
        
        pose_manager = maya_lib.corrective.PoseManager()
        pose_manager.set_pose_to_default()
        pose_manager.detach_poses()
        
        poses = pose_manager.get_poses()
        
        poses.append('pose_gr')
        
        if not poses:
            util.warning('Found no poses to export.')
            return
        
        for pose in poses:
            
            cmds.editDisplayLayerMembers("defaultLayer", pose)
            
            parent = None
            rels = None
            
            parent = cmds.listRelatives(pose, p = True)
            
            if parent:
                cmds.parent(pose, w = True)
                
            if pose == 'pose_gr':
                
                rels = cmds.listRelatives(pose)
                cmds.parent(rels, w = True)
            
            inputs = self._select_inputs(pose)
            self._filter_inputs(inputs)
            
            path = util_file.join_path(dir_path, '%s.ma' % pose)
            
            self._save_file(path)
            
            if parent:
                cmds.parent(pose, parent[0])
                
            if rels:
                cmds.parent(rels, 'pose_gr')
        
        pose_manager.attach_poses()
                
        util.show('Exported %s data.' % self.name)
    
    
    def import_data(self):
        
        path = util_file.join_path(self.directory, self.name)
        
        if not path:
            return
        
        if not util_file.is_dir(path):
            return  
        
        pose_files = util_file.get_files(path)
        
        if not pose_files:
            return
        
        poses = []
        
        cmds.renderThumbnailUpdate( False )
        
        for pose_file in pose_files:
            
            pose_path = util_file.join_path(path, pose_file)
            
            if util_file.is_file(pose_path):
                split_name = pose_file.split('.')
                
                pose = split_name[0]
                
                if cmds.objExists(pose):
                    cmds.delete(pose)
                
                if not cmds.objExists(pose):
        
                    if pose != 'pose_gr':
                        poses.append(pose)
        
                    self._import_file(pose_path)
        
        if cmds.objExists('pose_gr') and poses:
            cmds.parent(poses, 'pose_gr')
        
        pose_manager = maya_lib.corrective.PoseManager()
        
        pose_manager.attach_poses(poses)
        
        pose_manager.create_pose_blends(poses)
        
        pose_manager.set_pose_to_default()
                
        util.show('Imported %s data.' % self.name)
        
        cmds.dgdirty(a = True)
        cmds.renderThumbnailUpdate( True )
        
                
        
class MayaAttributeData(MayaCustomData):
    """
    maya.attributes
    Export attribute data on selected nodes.
    Import attribute data on all nodes exported, unless something is selected.
    """
    def _data_name(self):
        return 'attributes'
        
    def _data_type(self):
        return 'maya.attributes' 

    def _data_extension(self):
        return ''
    
    def import_data(self):
        """
        This will import all nodes saved to the data folder.
        You may need to delete folders of nodes you no longer want to import.
        """
        
        path = util_file.join_path(self.directory, self.name)
        
        selection = cmds.ls(sl = True)
        
        if selection:
            files = selection
            
        if not selection:
            files = util_file.get_files_with_extension('data', path)

        for filename in files:
            
            if not filename.endswith('.data'):
                filename = '%s.data' % filename
                
            filepath = util_file.join_path(path, filename)

            if not util_file.is_file(filepath):
                continue
            
            node_name = filename.split('.')[0]

            if not cmds.objExists(node_name):
                
                util.warning( 'Skipping attribute import for %s. It does not exist.' % node_name ) 
                continue
            
            lines = util_file.get_file_lines(filepath)
            
            for line in lines:
                
                if not line:
                    continue
                
                line_list = eval(line)
                
                try:
                    cmds.setAttr('%s.%s' % (node_name, line_list[0]), line_list[1])    
                except:
                    util.warning('\tCould not set %s to %s. Maybe it is locked or connected.' % (line_list[0], line_list[1]))
            
        self._center_view()

    def export_data(self, comment):
        """
        This will export only the currently selected nodes.
        """
        path = util_file.join_path(self.directory, self.name)
        
        if not util_file.is_dir(path):
            util_file.create_dir(self.name, self.directory)
        
        selection = cmds.ls(sl = True)
        
        if not selection:
            util.warning('Nothing selected. Please select at least one node to export attributes.')
            return
        
        for thing in selection:
            
            util.show('Exporting attributes on %s' % thing)
            
            filename = util_file.create_file('%s.data' % thing, path)

            lines = []
            
            attributes = cmds.listAttr(thing, scalar = True, m = True)
            
            shapes = maya_lib.core.get_shapes(thing)
            if shapes:
                shape = shapes[0]
                shape_attributes = cmds.listAttr(shape, scalar = True, m = True)
                
                if shape_attributes:
                    new_set = set(attributes).union(shape_attributes)

                    attributes = list(new_set)
            
            for attribute in attributes:
                
                attribute_name = '%s.%s' % (thing, attribute)
                
                value = cmds.getAttr(attribute_name)
                
                lines.append("[ '%s', %s ]" % (attribute, value))
            
            write_file = util_file.WriteFile(filename)
            write_file.write(lines)

        
class MayaFileData(MayaCustomData):
    
    maya_binary = 'mayaBinary'
    maya_ascii = 'mayaAscii'
        
    def __init__(self, name = None):
        super(MayaFileData, self).__init__(name)
        
        self.maya_file_type = self._set_maya_file_type()
    
    def _data_type(self):
        return 'maya.vtool'
        
    def _set_maya_file_type(self):
        
        return self.maya_binary
    
    def _clean_scene(self):
        
        maya_lib.core.delete_turtle_nodes()
        maya_lib.core.delete_garbage()

    def _prep_scene_for_export(self):
        outliner_sets = maya_lib.core.get_outliner_sets()
        top_nodes = maya_lib.core.get_top_dag_nodes()
        
        to_select = outliner_sets + top_nodes
        
        if not to_select:
            to_select = ['persp','side','top','front']
        
        cmds.select(to_select, r = True )
            
    def import_data(self, filepath = None):
        
        if open == True:
            self.open(filepath)
        
        import_file = None
        
        if filepath:
            import_file = filepath
            
        if not import_file:
            if not util_file.is_file(self.filepath):
                return
            
            import_file = self.filepath
        
        maya_lib.core.import_file(import_file)
        #cmds.file(import_file, f = True, i = True, iv = True)
        
        self._center_view()
        
    def open(self, filepath = None):
        
        open_file = None
        
        if filepath:
            open_file = filepath
            
        if not open_file:
            if not util_file.is_file(self.filepath):
                return
            
            open_file = self.filepath
        
        try:
            cmds.file(open_file, 
                      f = True, 
                      o = True, 
                      iv = True)
            
        except:
            
            util.show(traceback.format_exc())
            
        self._center_view()
       
    def save(self, comment):

        self._clean_scene()

        unknown = cmds.ls(type = 'unknown')
        
        if unknown:
            
            value = cmds.confirmDialog( title='Unknown Nodes!', 
                                        message= 'Unknown nodes usually happen when a plugin that was being used is not loaded.\nLoad the missing plugin, and the unknown nodes could become valid.\n\nDelete unknown nodes?\n', 
                                        button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
            
            if value == 'Yes':
                maya_lib.core.delete_unknown_nodes()
            
            if value == 'No':
                if self.maya_file_type == self.maya_binary:
                    cmds.warning('\tThis file contains unknown nodes. Try saving as maya ascii instead.')
                

        cmds.file(rename = self.filepath)
        
        #self._prep_scene_for_export()
        
        cmds.file(save = True,
                  prompt = False, 
                  force = True, 
                  pr = True, 
                  ch = True, 
                  chn = True, 
                  exp = True, 
                  con = True, 
                  stx = 'always', 
                  type = self.maya_file_type)
        
        version = util_file.VersionFile(self.filepath)
        version.save(comment)
        
    def export_data(self, comment):
        
        self._clean_scene()
        
        unknown = cmds.ls(type = 'unknown')
        
        if unknown:
            value = cmds.confirmDialog( title='Unknown Nodes!', 
                                        message= 'Unknown nodes usually happen when a plugin that was being used is not loaded.\nLoad the missing plugin, and the unknown nodes could become valid.\n\nDelete unknown nodes?\n', 
                                        button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
            
            if value == 'Yes':
                maya_lib.core.delete_unknown_nodes()
            
            if value == 'No':
                if self.maya_file_type == self.maya_binary:
                    cmds.warning('\tThis file contains unknown nodes. Try saving as maya ascii instead.')
        
        cmds.file(rename = self.filepath)
        
        self._prep_scene_for_export()
        
        cmds.file(exportSelected = True, 
                  prompt = False, 
                  force = True, 
                  pr = True, 
                  ch = True, 
                  chn = True, 
                  exp = True, 
                  con = True, 
                  stx = 'always', 
                  type = self.maya_file_type)
        
        version = util_file.VersionFile(self.filepath)
        version.save(comment)

    def maya_reference_data(self, filepath = None):
        
        if not filepath:
            filepath = self.filepath
        
        maya_lib.core.reference_file(filepath)
        
    def set_directory(self, directory):
        super(MayaFileData, self).set_directory(directory)
        
        self.filepath = util_file.join_path(directory, '%s.%s' % (self.name, self.data_extension))

class MayaBinaryFileData(MayaFileData):
    
    def _data_type(self):
        return 'maya.binary'
    
    def _data_extension(self):
        return 'mb'
        
    def _set_maya_file_type(self):
        return self.maya_binary
    
class MayaAsciiFileData(MayaFileData):
    
    def _data_type(self):
        return 'maya.ascii'
    
    def _data_extension(self):
        return 'ma'
    
    def _set_maya_file_type(self):
        return self.maya_ascii
    
