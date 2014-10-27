# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import traceback
import threading

import util        
import util_file

if util.is_in_maya():
    import maya.cmds as cmds
    import maya.mel as mel
    
    import maya_lib.util
    import maya_lib.curve

class DataManager(object):
    
    def __init__(self):
        self.available_data = [MayaAsciiFileData(), 
                               MayaBinaryFileData(), 
                               ScriptManifestData(),
                               ScriptPythonData(),
                               ControlCvData(),
                               SkinWeightData(),
                               AnimationData(),
                               AtomData(),
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
        
        if util_file.is_dir(test_path):
            self.folder_path = test_path
            self._load_folder()
        
        if not util_file.is_dir(test_path):
            self._create_folder()
        
    def _load_folder(self):
        self._set_default_settings()
        
    def _set_settings_path(self, folder):
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
        self.name = name
        self.settings.set('name', str(self.name))
        
                
    def get_data_type(self):
        return self.settings.get('data_type')
    
    def set_data_type(self, data_type):

        self.data_type = data_type
        self.settings.set('data_type', str(data_type))
        
    def get_folder_data_instance(self):
        
        if not self.name:
            return
        
        data_type = self.settings.get('data_type')
        
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
        
        #path = vtool.create_dir(name, self.directory)
        
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
        write_file.write(lines)
        
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
        except:
            #do not remove print
            print 'Could not center view.'
      
class ControlCvData(MayaCustomData):
    def _data_name(self):
        return 'control_cvs'
        
    def _data_type(self):
        return 'maya.control_cvs'
    
    def import_data(self):
        
        
        controls = maya_lib.util.get_controls()

        library = maya_lib.curve.CurveDataInfo()
        library.set_directory(self.directory)
        library.set_active_library(self.name)
            
        for control in controls:
            shapes = maya_lib.util.get_shapes(control)
            if shapes:
                library.set_shape_to_curve(shapes[0], control, True)
                
        self._center_view()
    
    def export_data(self, comment):
        
        library = maya_lib.curve.CurveDataInfo()
        controls = maya_lib.util.get_controls()
        
        library.set_directory(self.directory)
        library.set_active_library(self.name)
        
        for control in controls:
                     
            shapes = maya_lib.util.get_shapes(control)          
            
            if shapes:
                library.add_curve(shapes[0])
            if not shapes:
                maya_lib.util.warning("No shape node for: %s' % control")
            
        filepath = library.write_data_to_file()
        
        version = util_file.VersionFile(filepath)
        version.save(comment)
          
class SkinWeightData(MayaCustomData):

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
            influence_dict = read_thread.run(influence_dict, folder_path, influence)
                    
        return influence_dict
        
    def import_data(self):
        
        path = util_file.join_path(self.directory, self.name)
        
        selection = cmds.ls(sl = True)
        
        if selection:
            folders = selection
            
        if not selection:
            folders = util_file.get_folders(path)
        
        if not folders:
            return
        
        cmds.undoInfo(state = False)
        
        for folder in folders:
            
            mesh = folder
            
            if not cmds.objExists(mesh):
                continue
            
            skin_cluster = maya_lib.util.find_deformer_by_type(mesh, 'skinCluster')
            
            folder_path = util_file.join_path(path, folder)
            
            influence_dict = self._get_influences(folder_path)

            influences = influence_dict.keys()
            influences.sort()
            
            available_influences = []
            for influence in influences:
                if cmds.objExists(influence):
                    available_influences.append(influence)
            
            skip = False
            
            if not skin_cluster:
                
                if not available_influences:
                    cmds.undoInfo(state = True)
                    skip = True
                
                if available_influences:
                    skin_cluster = cmds.skinCluster(available_influences, mesh,  tsb = True)[0]
            
            if skip == True:
                continue
                
            cmds.setAttr('%s.normalizeWeights' % skin_cluster, 0)
            
            maya_lib.util.set_skin_weights_to_zero(skin_cluster)
            cmds.refresh()
             
            influence_index_dict = maya_lib.util.get_skin_influences(skin_cluster, return_dict = True)
            
            influence_inc = 0
            
            progress_ui = maya_lib.util.ProgressBar('import skin', len(influence_dict.keys()))
            
            for influence in influences:
                
                progress_ui.status('importing skin mesh: %s,  influence: %s' % (mesh, influence))
                
                if not cmds.objExists(influence):
                    cmds.select(cl = True)
                    cmds.joint( n = influence, p = influence_dict[influence]['position'] )
                    cmds.skinCluster(skin_cluster, e = True, ai = influence)  
                    
                    influence_index_dict = maya_lib.util.get_skin_influences(skin_cluster, return_dict = True)
                
                weights = influence_dict[influence]['weights']
                
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
            
        cmds.undoInfo(state = True)
        
        self._center_view()
                    
    def export_data(self, comment):
        
        print 'exporting data'
        
        path = util_file.join_path(self.directory, self.name)
        
        selection = cmds.ls(sl = True)
        
        for thing in selection:
            skin = maya_lib.util.find_deformer_by_type(thing, 'skinCluster')
            
            if skin:
                
                geo_path = util_file.join_path(path, thing)
                
                if util_file.is_dir(geo_path):
                    util_file.delete_dir(thing, path)
                
                geo_path = util_file.create_dir(thing, path)
                
                weights = maya_lib.util.get_skin_weights(skin)
                
                info_file = util_file.create_file( 'influence.info', geo_path )
                
                write_info = util_file.WriteFile(info_file)
                info_lines = []
                
                for influence in weights:
                    
                    print 'influence!', influence
                    
                    weight_list = weights[influence]
                    
                    if influence == 85:
                        print 'WEIGHTS!'
                        print weight_list
                    
                    if not weight_list:
                        continue
                    
                    thread = LoadWeightFileThread()
                    influence_line = thread.run(influence, skin, weights[influence], geo_path)
                    
                    info_lines.append(influence_line)
                
                    
                write_info.write(info_lines)
             
class LoadWeightFileThread(threading.Thread):
    def __init__(self):
        super(LoadWeightFileThread, self).__init__()
        
    def run(self, influence_index, skin, weights, path):
        
        influence_name = maya_lib.util.get_skin_influence_at_index(influence_index, skin)
        
        print influence_name
        
        filepath = util_file.create_file('%s.weights' % influence_name, path)
        
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
    

class MayaShadersData(CustomData):
    
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
    
    def _data_name(self):
        return 'animation'
    
    def _data_type(self):
        return 'maya.animation'
    
    def export_data(self, comment):
        
        keyframes = cmds.ls(type = 'animCurve')
        
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
            
            inputs = maya_lib.util.get_attribute_input('%s.input' % keyframe)
            outputs = maya_lib.util.get_attribute_outputs('%s.output' % keyframe)
                        
            if not inputs and not outputs:
                continue
                        
            cmds.select(keyframe, add = True)
            
            connections = maya_lib.util.Connections(keyframe)
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
        
    def import_data(self):
        
        path = util_file.join_path(self.directory, 'keyframes')
        
        filepath = util_file.join_path(path, 'keyframes.ma')
            
        info_file = util_file.join_path(path, 'animation.info')
        info_lines = util_file.get_file_lines(info_file)
        
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
                    try:
                        cmds.connectAttr('%s.output' % key, output)
                    except:
                        #do not remove print
                        print 'Could not connect %s.output to %s' % (key,output)            

            input_attr = keyframes['input']
            
            if input_attr:
                
                if not cmds.objExists(input_attr):
                    continue
                try:
                    cmds.connectAttr(input_attr, '%s.input' % key)
                except:
                    #do not remove print
                    print 'Could not connect %s to %s.input' % (input_attr,key)
        


                

        
class AtomData(MayaCustomData):

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

    maya_binary = 'mayaBinary'

    def _data_name(self):
        return 'pose'

    def _data_extension(self):
        return ''
    
    def _data_type(self):
        return 'maya.pose' 

    def _save_file(self, filepath):
        cmds.file(rename = filepath)
        
        cmds.file(exportSelected = True, prompt = False, force = True, pr = True, ch = False, chn = True, exp = True, con = False, stx = 'always', typ = self.maya_binary, sh = False)
        
    def _import_file(self, filepath):
                
        if util_file.is_file(filepath):
            cmds.file(filepath, f = True, i = True, iv = True, shd = 'shadingNetworks')
        
        if not util_file.is_file(filepath):
            mel.eval('warning "File does not exist"')

    def export_data(self, comment):
        
        dir_path = util_file.join_path(self.directory, self.name)
        
        pose_manager = maya_lib.util.PoseManager()
        pose_manager.detach_poses()
        
        poses = pose_manager.get_poses()
        
        poses.append('pose_gr')
        
        for pose in poses:
            parent = None
            rels = None
            
            parent = cmds.listRelatives(pose, p = True)
            
            if parent:
                cmds.parent(pose, w = True)
                
            if pose == 'pose_gr':
                rels = cmds.listRelatives(pose)
                
                cmds.parent(rels, w = True)
            
            inputs = maya_lib.util.get_inputs(pose)
            outputs = maya_lib.util.get_outputs(pose)

            if inputs:
                inputs.append(pose)

            if not inputs:
                inputs = [pose]
            
            if outputs:
                inputs = inputs + outputs

            path = util_file.join_path(dir_path, '%s.mb' % pose)                              
            
            cmds.select(cl = True)
            cmds.select(inputs, ne = True)
            
            self._save_file(path)
            
            if parent:
                cmds.parent(pose, parent[0])
                
            if rels:
                cmds.parent(rels, 'pose_gr')
    
    def import_data(self):
        path = util_file.join_path(self.directory, self.name)
        
        if not path:
            return        
        
        pose_files = util_file.get_files(path)
        
        if not pose_files:
            return
        
        poses = []
        
        for pose_file in pose_files:
            pose_path = util_file.join_path(path, pose_file)
            
            if util_file.is_file(pose_path):
                split_name = pose_file.split('.')
                
                pose = split_name[0]
                
                if not cmds.objExists(pose):
        
                    if pose != 'pose_gr':
                        poses.append(pose)
        
                    self._import_file(pose_path)
                    
        if cmds.objExists('pose_gr'):
            cmds.parent(poses, 'pose_gr')
        
        pose_manager = maya_lib.util.PoseManager()
        pose_manager.attach_poses()
        pose_manager.create_pose_blends()
        pose_manager.set_pose_to_default()
        
class MayaAttributeData(MayaCustomData):
    def _data_name(self):
        return 'attributes'
        
    def _data_type(self):
        return 'maya.attributes' 

    def _data_extension(self):
        return ''

    def import_data(self):
        
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
                #do not remove print
                print 'Could not import attributes for %s' % node_name
                continue
            
            lines = util_file.get_file_lines(filepath)
            
            
            
            for line in lines:
                
                if not line:
                    continue
                
                line_list = eval(line)
                
                try:
                    cmds.setAttr('%s.%s' % (node_name, line_list[0]), line_list[1])    
                except:
                    #do not remove print
                    print 'Could not set %s to %s' % (line_list[0], line_list[1])
            
        self._center_view()

    def export_data(self, comment):
        
        path = util_file.join_path(self.directory, self.name)
        
        if not util_file.is_dir(path):
            util_file.create_dir(self.name, self.directory)
        
        selection = cmds.ls(sl = True)
        
        for thing in selection:
            
            filename = util_file.create_file('%s.data' % thing, path)

            lines = []
            
            attributes = cmds.listAttr(thing, scalar = True, m = True)
            
            for attribute in attributes:
                attribute_name = '%s.%s' % (thing, attribute)
                
                """
                pass_types = ['float3', 'TdataCompound']
                attribute_type = cmds.getAttr(attribute_name, type = True)
                
                skip = False
                
                for pass_type in pass_types:
                    if pass_type == attribute_type:
                        skip = True
                    
                if skip:
                    continue
                """
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
    
    def _prep_scene_for_export(self):
        outliner_sets = maya_lib.util.get_outliner_sets()
        top_nodes = maya_lib.util.get_top_dag_nodes()
        
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
        
        cmds.file(import_file, f = True, i = True, iv = True)
        
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
            
        except Exception:
            #do not remove print
            print traceback.format_exc()
        
        self._center_view()
       
    def save(self, comment):

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
    
