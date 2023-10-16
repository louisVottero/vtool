from vtool import util


class PlatformUtilRig(object):

    def __init__(self):

        self.rig = None

    def __getattribute__(self, item):

        custom_functions = ['build']

        if item in custom_functions:

            if item == 'build':
                result = self._pre_build()
                if result == False:
                    return lambda *args: None

            result = object.__getattribute__(self, item)

            result_values = result()

            def results():
                return result_values

            if item == 'build':
                self._post_build()

            return results

        else:

            return object.__getattribute__(self, item)

    def _pre_build(self):
        # util.show('\t\tPre Build Rig: %s' % self.__class__.__name__)
        return

    def _post_build(self):
        # util.show('\t\tPost Build Rig: %s' % self.__class__.__name__)
        return

    def set_rig_class(self, rig_class_instance):
        self.rig = rig_class_instance

    def load(self):
        util.show('\t\tLoad Rig: %s %s' % (self.__class__.__name__, self.rig.uuid))
        pass

    def build(self):
        util.show('\t\tBuild Rig: %s' % self.__class__.__name__)
        pass

    def unbuild(self):
        pass

    def delete(self):
        pass
