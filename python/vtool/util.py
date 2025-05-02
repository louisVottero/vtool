# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import print_function
from __future__ import absolute_import

import sys

python_version = float('%s.%s' % (sys.version_info.major, sys.version_info.minor))

import re
import fnmatch
import time
import datetime
import traceback
import platform
import os
import base64

if python_version < 3:
    from HTMLParser import HTMLParser
    import __builtin__ as py_builtins
    string_types = (str, unicode)
else:
    from html.parser import HTMLParser
    import builtins as py_builtins
    string_types = (str,)

from functools import wraps

import subprocess

try: import maya.cmds as cmds; in_maya = True
except ImportError: in_maya = False

try: import unreal; in_unreal = True
except ImportError: in_unreal = False

try: import hou; in_houdini = True
except ImportError: in_houdini = False

try: import nuke; in_nuke = True
except ImportError: in_nuke = False

temp_log = ''
last_temp_log = ''

global_tabs = 1

if in_maya:
    if python_version < 3:
        import pymel.all as pymel
    else:
        pymel = None


def get_dirname():
    return os.path.dirname(__file__)


def get_custom(name, default=''):
    """
    Get a value from __custom__ module if it exists, otherwise return default.
    """
    try:
        from vtool import __custom__
        value = getattr(__custom__, name, default)
        return value if value else default
    except ImportError:
        return default


def stop_watch_wrapper(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        class_name = None
        if args:
            if hasattr(args[0], '__class__'):
                class_name = args[0].__class__.__name__
        watch = StopWatch()
        description = function.__name__
        if class_name:
            description = class_name + '.' + description

        watch.start(description, feedback=False)
        watch.feedback = True

        return_value = None

        try:
            return_value = function(*args, **kwargs)
        except:
            error(traceback.format_exc())

        watch.end()

        return return_value

    return wrapper


class VetalaHTMLParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self._in_body = False
        self.all_body_data = []

    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self._in_body = True
        elif self._in_body and tag == 'img':
            attrs_dict = dict(attrs)
            if 'src' in attrs_dict:
                self.all_body_data.append({'img': attrs_dict['src']})

    def handle_endtag(self, tag):
        if tag == 'body':
            self._in_body = False

    def handle_data(self, data):
        data = data.strip()
        if data and self._in_body:
            self.all_body_data.append({'text': data})

    def get_body_data(self):
        return self.all_body_data


class ControlName(object):
    CONTROL_ALIAS = 'Control Alias'
    DESCRIPTION = 'Description'
    NUMBER = 'Number'
    SIDE = 'Side'

    def __init__(self):

        self.control_alias = 'CNT'
        self.center_alias = 'C'
        self.left_alias = 'L'
        self.right_alias = 'R'

        self.control_order = [self.CONTROL_ALIAS, self.DESCRIPTION, self.NUMBER, self.SIDE]

        self.control_uppercase = True

        self._control_number = True
        self.use_side_alias = True

    def set_control_alias(self, alias):
        self.control_alias = str(alias)

    def set_left_alias(self, alias):
        self.left_alias = str(alias)

    def set_right_alias(self, alias):
        self.right_alias = str(alias)

    def set_center_alias(self, alias):
        self.center_alias = str(alias)

    def set_use_side_alias(self, bool_value):
        self.use_side_alias = bool_value

    def set_uppercase(self, bool_value):
        self.control_uppercase = bool_value

    def set_control_order(self, list_value):
        self.control_order = list_value

    def set_number_in_control_name(self, bool_value):
        self._control_number = bool_value

    def get_name(self, description, side=None):

        found = []
        found_side = ''

        if not self.control_order:
            return

        for name in self.control_order:
            if name == self.CONTROL_ALIAS:
                found.append(self.control_alias)
            if name == self.DESCRIPTION:
                if description:
                    found.append(description)
            if name == self.NUMBER and self._control_number == True:
                found.append(str(1))
            if name == self.SIDE:
                if not side:
                    continue
                if self.use_side_alias:
                    if is_left(side):
                        found.append(self.left_alias)
                        found_side = found[-1]
                        continue
                    if is_right(side):
                        found.append(self.right_alias)
                        found_side = found[-1]
                        continue
                    if is_center(side):
                        found.append(self.center_alias)
                        found_side = found[-1]
                        continue
                else:
                    found.append(side)
                    found_side = found[-1]
        full_name = '_'.join(found)
        if found_side:

            test_side = '_%s_' % found_side

            if full_name.find(test_side) > -1:
                full_name = full_name.replace(test_side, '_')

        if self.control_uppercase:
            full_name = full_name.upper()

        return full_name


def get_code_builtins():
    builtins = {'show': show,
                'warning': warning}

    if in_maya:
        maya_builtins = {'cmds': cmds,
                         'mc': cmds,
                         'pymel': pymel,
                         'pm': pymel}

        for builtin in maya_builtins:
            builtins[builtin] = maya_builtins[builtin]

    return builtins


def reset_code_builtins(builtins=None):
    """
    Remove specified custom builtins from the global builtins module.

    Args:
        builtins (list or set): Names of builtins to remove. Defaults to `get_code_builtins().keys()`.
    """
    if not builtins:
        builtins = get_code_builtins().keys()

    for name in builtins:
        try:
            delattr(py_builtins, name)
        except AttributeError:
            pass


def setup_code_builtins(builtin=None):
    """
    Set up custom builtins for the current Python environment.

    Args:
        builtin (dict): A dictionary of builtins to set. Defaults to `get_code_builtins()`.
    """
    if builtin is None:
        builtin = get_code_builtins()

    for name, value in builtin.items():
        try:
            setattr(py_builtins, name, value)
        except Exception as e:
            error("Failed to set builtin '%s': %s" % (name, str(e)))


def initialize_env(name):
    """
    Initialize a new environment variable.
    If the variable already exists, does nothing, no environment variable is initialized.

    Args:
        name (str): Name of the new environment variable.
    """
    if name not in os.environ:
        os.environ[name] = ''


def get_env(name):
    """
    Get the value of an environment variable.

    Args:
        name (str): Name of an environment variable.

    Returns
        str:
    """
    if name in os.environ:
        return os.environ[name]


def set_env(name, value):
    """
    Set the value of an environment variable.

    Args:
        name (str): Name of the environment variable to set.
        value (str): If a number is supplied it will automatically be converted to str.
    """

    value = str(value)

    size = sys.getsizeof(value)
    if size > 32767:
        value = value[:30000]
        value = 'truncated... ' + value
    os.environ[name] = value


def suggest_env(name, value):
    if name not in os.environ:
        set_env(name, value)


def start_temp_log():
    set_env('VETALA_KEEP_TEMP_LOG', 'True')
    global temp_log
    temp_log = ''


def record_temp_log(value):
    global temp_log
    if os.environ.get('VETALA_KEEP_TEMP_LOG') == 'True':
        value = value.replace('\t', '  ')
        temp_log += value


def end_temp_log():
    global temp_log
    global last_temp_log

    set_env('VETALA_KEEP_TEMP_LOG', 'False')
    value = temp_log
    if value:
        last_temp_log = temp_log

        temp_log = ''

    return value


def get_last_temp_log():
    global last_temp_log
    return last_temp_log


def add_to_PYTHONPATH(path):
    """
    Add a path to the python path, only if it isn't present in the python path.

    Args:
        path (str): The path to add to the python path.
    """
    if not path:
        return
    elif path not in sys.path:
        sys.path.append(path)


def profiler_event(frame, event, arg, indent=None):
    if indent is None:
        indent = [0]
    if event == "call":
        indent[0] += 2
        print("-" * indent[0] + "> ", event, frame.f_code.co_name)
    elif event == "return":
        print("<" + ("-" * indent[0]) + " ", event, frame.f_code.co_name)
        indent[0] -= 2

    return profiler_event


def activate_profiler():
    """
    Activating the profiler will give extremely detailed information about what functions are running and in what order.
    """
    sys.setprofile(profiler_event)


#--- decorators
def try_pass(function):
    """
    Try a function and if it fails pass.  Used as a decorator.
    Usage:
    @try_pass
    def myFunction():
        do_something
    """

    def wrapper(*args, **kwargs):

        return_value = None

        try:
            return_value = function(*args, **kwargs)
        except:
            error(traceback.format_exc())

        return return_value

    return wrapper

#---  query


def is_str(value):
    return isinstance(value, string_types)


def is_iterable(obj):
    try:
        iter(obj)
        return True
    except TypeError:
        return False


def is_stopped():
    return os.environ.get('VETALA_STOP') == 'True'


def is_in_maya():
    return in_maya


def is_in_unreal():
    return in_unreal


def is_in_houdini():
    return in_houdini


def has_shotgun_api():
    """
    Check if the shotgun api is available.

    Returns:
        bool:
    """
    try:
        import shotgun_api3
        return True
    except:
        return False


def has_shotgun_tank():
    """
    Check if the shotgun tank api is available.

    Returns:
        bool:
    """
    try:
        # import tank
        import sgtk
        return True
    except:
        return False


def get_current_maya_location():
    """
    Get where maya is currently running from.
    """
    location = os.environ.get('MAYA_LOCATION', '')
    return location


def is_in_nuke():
    """
    Check to see if scope is in Nuke

    Returns:
        bool:
    """
    return in_nuke


def is_linux():
    """
    Check to see if running in linux

    Returns:
        bool:
    """
    return platform.system() == 'Linux'


def is_windows():
    """
    Check to see if running in windows

    Returns:
        bool:
    """
    return platform.system() == 'Windows'


def get_maya_version():
    """
    Get the version of maya that the scope is running in.

    Returns:
        int: The date of the Maya version.
    """

    if in_maya:
        try:
            version = str(cmds.about(api=True))[:4]
            version = int(version)

            return version
        except:
            show('Could not get maya version.')
    else:
        return 0


def get_unreal_version():
    if in_unreal:
        version = unreal.SystemLibrary.get_engine_version()
        split_version = version.split('.')

        return [int(split_version[0]), int(split_version[1])]


def break_signaled():
    """
    Check to see if Vetala break was signalled.

    Returns:
        bool:
    """
    return os.environ.get('VETALA_RUN') == 'True' and os.environ.get('VETALA_STOP') == 'True'

#--- output


def get_tabs():
    tab_text = '\t' * global_tabs
    return tab_text


def get_log_tabs():
    log_tabs = 0

    if global_tabs > 1:
        log_tabs = global_tabs * 2

    tab_text = '\t' * (log_tabs - 1)
    return tab_text


def show_list_to_string(*args):
    try:
        if args is None:
            return 'None'

        if not args:
            return ''

        new_args = []

        for arg in args:
            if arg is not None:
                new_args.append(str(arg))

        args = new_args

        if not args:
            return ''

        string_value = ' '.join(args)

        string_value = string_value.replace('\n', '\t\n')
        if string_value.endswith('\t\n'):
            string_value = string_value[:-2]

        return string_value
    except:
        raise RuntimeError


def show(*args):
    log_value = None
    text = ''
    tab_str = None

    try:
        tab_str = get_tabs()
        log_tab_str = get_log_tabs()
        string_value = show_list_to_string(*args)
        log_value = string_value

        string_value = string_value.replace('\n', '\nV:%s\t' % tab_str)
        text = 'V:%s\t%s' % (tab_str, string_value)

        record_temp_log('\n%s%s' % (log_tab_str, log_value))

    except:
        # do not remove
        text = 'V:%s\tCould not show %s' % (tab_str, args)

        record_temp_log('\n%s%s' % (tab_str, log_value))
        raise RuntimeError('Error showing')

    if text:

        if in_unreal:
            unreal.log(text)
        else:
            # do not remove
            print(text)


def warning(*args):
    try:
        string_value = show_list_to_string(*args)
        string_value = string_value.replace('\n', '\nV:\t\t')

        text = 'V: Warning!\t%s' % string_value
        # do not remove
        if in_unreal:
            unreal.log_warning(text)
        elif in_maya:
            cmds.warning('V: \t%s' % string_value)
        else:
            print(text)
        record_temp_log('\nWarning!:  %s' % string_value)

    except:
        raise RuntimeError


def error(*args):
    try:
        string_value = show_list_to_string(*args)
        string_value = string_value.replace('\n', '\nV:\t\t')

        text = 'V: Error!\t%s' % string_value
        if in_unreal:
            unreal.log_error(text)
        else:
            # do not remove
            print(text)

        record_temp_log('\n%s' % string_value)

    except:
        raise RuntimeError


def stack_trace():
    stack_trace = traceback.format_stack()

    return  ''.join(stack_trace[:-1])


class StopWatch(object):
    """
    Utility to check how long a command takes to run.
    """

    running = 0
    watch_list = []

    def __del__(self):
        pass

    def __init__(self):
        self.time = None
        self.feedback = True
        self.description = ''
        self.round = 2
        self.enable = True

    def start(self, description='', feedback=True):

        if not self.enable:
            return

        self.__class__.running += 1
        self.running = self.__class__.running - 1

        self.description = description
        self.feedback = feedback

        if feedback:
            tabs = '\t' * self.running
            show('%sStarted timer:' % tabs, description)

        self.time = time.time()

        self.__class__.watch_list.append([description, self.time])

    def end(self, show_elapsed_time=True):

        if not self.enable:
            return

        self.description, self.time = self.__class__.watch_list[self.running]

        if not self.time:
            if self.running > 0:
                self.__class__.running -= 1
                self.running -= 1
            return

        seconds = time.time() - self.time
        self.time = None

        seconds = round(seconds, self.round)
        minutes = None

        if seconds > 60:
            minutes, seconds = divmod(seconds, 60)
            seconds = round(seconds, self.round)
            minutes = int(minutes)

        if self.feedback:
            tabs = '\t' * self.running
            show_result = ''

            if minutes is None:
                show_result = '%sIt took %s: %s seconds' % (tabs, self.description, seconds)
            else:
                if minutes > 1:
                    show_result = '%sIt took %s: %s minutes, %s seconds' % (tabs, self.description, minutes, seconds)
                if minutes == 1:
                    show_result = '%sIt took %s: %s minute, %s seconds' % (tabs, self.description, minutes, seconds)

            if show_elapsed_time:
                show(show_result)

        self.__class__.watch_list.pop()

        if self.running > 0:
            self.running -= 1

        self.__class__.running -= 1

        return minutes, seconds

    def stop(self):
        if not self.enable:
            return
        return self.end()


class Variable(object):
    """
    Simple base class for variables on a node.

    Args:
        name (str): The name of the variable.
    """

    def __init__(self, name='empty'):
        self.name = name
        self.value = 0
        self.node = None

    def set_node(self, node_name):
        """
        Set the node to work on.

        Args:
            node_name (str)
        """
        self.node = node_name

    def set_name(self, name):
        """
        Set the name of the variable.

        Args:
            name (str): The name to give the variable.
        """

        self.name = name

    def set_value(self, value):
        """
        Set the value that the variable holds.

        Args:
            value
        """
        self.value = value

    def create(self, node):
        raise NotImplementedError("The 'create' method must be implemented in a subclass.")

    def delete(self, node):
        raise NotImplementedError("The 'create' method must be implemented in a subclass.")


class Part(object):

    def __init__(self, name):
        self.name = name

    def _set_name(self, name):
        self.name = name

    def create(self):
        pass

    def delete(self):
        pass


def convert_to_sequence(variable, sequence_type=list):  # TODO: There are a ton of calls to this that dont need to exist if one just uses the respective literal.
    """
    Easily convert to a sequence.
    If variable is already of sequence_type, pass it through.
    If variable is a list and sequence_type is tuple, convert to tuple.
    If variable is a tuple and sequence_type is list, convert to list.
    If variable is not a list or tuple, then create a sequence of sequence type.

    Basically insures that a variable is a list or a tuple.

    Args:

        variable: Any variable.
        sequence_type: Can either be python list or python tuple. Needs to be the type object, which means pass it list or tuple not as a string.

    Returns:
        list, tuple: Returns list or tuple depending on the sequence_type.
    """

    if isinstance(variable, sequence_type):
        return variable
    elif isinstance(variable, list) and sequence_type is tuple:
        variable = tuple(variable)
        return variable
    elif isinstance(variable, tuple) and sequence_type is list:
        variable = list(variable)
        return variable
    elif not isinstance(variable, sequence_type):
        if not variable and variable != 0:
            if sequence_type is list:
                return []
            if sequence_type is tuple:
                return ()
        else:
            if sequence_type is list:
                return [variable]
            if sequence_type is tuple:
                return (variable,)

    return variable


def convert_str_to_list(str_value):

    split_str = str_value.split()

    found = []

    for split in split_str:
        if not split:
            continue
        if split.find(',') > -1:
            new_value = split.split(',')
            for sub_value in new_value:
                if sub_value:
                    found.append(sub_value)
        else:
            found.append(split)

    return found


def uv_to_udim(u, v):
    number = int(1000 + (u + 1) + (v * 10))

    return number

#--- time


def convert_number_to_month(month_int):
    months = ('January',
              'February',
              'March',
              'April',
              'May',
              'June',
              'July',
              'August',
              'September',
              'October',
              'November',
              'December')

    month_int -= 1

    if month_int < 0 or month_int > 11:
        return

    return months[month_int]


def get_current_time(date_and_time=True):
    mtime = time.time()

    date_value = datetime.datetime.fromtimestamp(mtime)

    hour = str(date_value.hour)
    minute = str(date_value.minute)
    second = date_value.second

    second = str(int(second))

    if len(hour) == 1:
        hour = '0' + hour
    if len(minute) == 1:
        minute = '0' + minute
    if len(second) == 1:
        second = second + '0'

    time_value = '%s:%s:%s' % (hour, minute, second)

    if date_and_time:
        year = date_value.year
        month = date_value.month
        day = date_value.day
        return '%s-%s-%s %s' % (year, month, day, time_value)
    else:
        return time_value


def get_current_date():
    mtime = time.time()
    date_value = datetime.datetime.fromtimestamp(mtime)
    year = date_value.year
    month = date_value.month
    day = date_value.day

    return '%s-%s-%s' % (year, month, day)

#--- strings


class FindUniqueString(object):

    def __init__(self, test_string):
        self.test_string = test_string
        self.increment_string = None
        self.padding = 0

    def _get_scope_list(self):
        return []

    def _format_string(self, number):

        if number == 0:
            number = 1

        exp = search_last_number(self.test_string)

        if self.padding:
            number = str(number).zfill(self.padding)

        if exp:
            self.increment_string = '%s%s%s' % (self.test_string[:exp.start()], number, self.test_string[exp.end():])
        else:
            split_dot = self.test_string.split('.')

            if len(split_dot) > 1:
                split_dot[-2] += str(number)

                self.increment_string = '.'.join(split_dot)

            if len(split_dot) == 1:
                self.increment_string = '%s%s' % (self.test_string, number)

    def _get_number(self):

        return get_end_number(self.test_string)

    def _search(self):

        number = self._get_number()

        self.increment_string = self.test_string

        unique = False

        while not unique:

            scope = self._get_scope_list()

            if not scope:
                unique = True
                continue

            if self.increment_string not in scope:
                unique = True
                continue

            if self.increment_string in scope:

                if not number:
                    number = 0

                self._format_string(number)

                number += 1
                unique = False

                continue

        return self.increment_string

    def set_padding(self, int_value):
        self.padding = int_value

    def get(self):
        return self._search()


def get_numbers(input_string):
    return list(map(int, re.findall(r'\d+', input_string)))


def get_float_numbers(input_string):
    pattern = re.compile(r'[-\d.]+')
    numbers = [float(n) for n in pattern.findall(input_string)]
    return numbers


def get_split_string_and_numbers(input_string):

    parts = re.split(r'(\d+)', input_string)
    key_parts = [(int(part) if part.isdigit() else part) for part in parts if part]

    return key_parts


def get_first_number(input_string, as_string=False):
    found = re.search('[0-9]+', input_string)

    if found:
        number_str = found.group()

        if as_string:
            return number_str

        number = int(number_str)

        return number


def get_last_number(input_string):
    search = search_last_number(input_string)
    if not search:
        return None

    found_string = search.group()
    number = None
    if found_string:
        number = int(found_string)

    return number


def get_last_letter(input_string):
    search = search_last_letter(input_string)

    if not search:
        return None

    found_string = search.group()

    return found_string


def get_end_number(input_string, as_string=False):
    """
    Get the number at the end of a string.

    Args:
        input_string (str): The string to search for a number.
        as_string (bool): TODO: Fill in description.

    Returns:
        int: The number at the end of the string.
    """
    number = re.findall('\d+', input_string)

    if number:
        if isinstance(number, list):
            number = number[0]

        if as_string:
            return number

        number = int(number)

    if number == []:
        number = 1

    return number


def get_trailing_number(input_string, as_string=False, number_count=-1):
    """
    Get the number at the very end of a string. If number not at the end of the string return None.
    """

    if not input_string:
        return

    number = '\d+'

    if number_count > 0:
        number = '\d' * number_count

    group = re.match('([a-zA-Z_0-9]+)(%s$)' % number, input_string)

    if group:
        number = group.group(2)
        if as_string:
            return number
        else:
            return int(number)


def search_first_number(input_string):
    expression = re.compile('[0-9]+')
    return expression.search(input_string)


def search_last_number(input_string):
    """
    Get the last number in a string.

    Args:
        input_string (str): The string to search for a number.

    Returns:
        int: The last number in the string.
    """
    expression = re.compile('(\d+)(?=(\D+)?$)')
    return expression.search(input_string)


def search_last_letter(input_string):
    """
    Get the last letter in a string.

    Args:
        input_string (str): The string to search for a number.

    Returns:
        int: The last number in the string.
    """

    match = re.findall('[_a-zA-Z]+', input_string)
    if match:
        return match[-1][-1]


def replace_last_number(input_string, replace_string):
    """
    Replace the last number with something.

    Args:
        input_string (str): A string to search for the last number.
        replace_string (str): The string to replace the last number with.

    Returns:
        str: The new string after replacing.
    """

    replace_string = str(replace_string)

    expression = re.compile('(\d+)(?=(\D+)?$)')
    search = expression.search(input_string)

    if not search:
        return input_string + replace_string

    return input_string[:search.start()] + replace_string + input_string[search.end():]


def increment_first_number(input_string):
    search = search_first_number(input_string)
    new_string = None

    if search:
        new_string = '%s%s%s' % (input_string[0: search.start()],
                                 int(search.group()) + 1,
                                 input_string[search.end():]
                                 )
    else:
        new_string = input_string + '_1'
    return new_string


def increment_last_number(input_string, padding=1):
    """
    Up the value of the last number by 1.

    Args:
        input_string (str): The string to search for the last number.
        padding (int): TODO: Fill description.

    Returns:
        str: The new string after the last number is incremented.
    """
    search = search_last_number(input_string)
    new_string = None
    if search:
        new_string = '%s%s%s' % (input_string[0: search.start()],
                                 str(int(search.group()) + 1).zfill(padding),
                                 input_string[search.end():]
                                 )
    else:
        new_string = input_string + '1'.zfill(padding)
    return new_string


def find_special(pattern, string_value, position_string):
    """
    Args:
        pattern (str): A regular expression pattern to search for.
        string_value (str): The string to search in.
        position_string (str): 'start','end','first','last','inside' Where the pattern should search.

    Returns:
        tuple: (start_int, end_int) The start and end index of the found pattern. Returns (None,None) if nothing found.
    """

    char_count = len(string_value)

    found_iter = re.finditer(pattern, string_value)

    found = []
    index_start = None
    index_end = None

    for item in found_iter:
        found.append(item)

    if not found:
        return None, None

    if position_string == 'end':
        index_start = found[-1].start()
        index_end = found[-1].end()
        if index_end > char_count or index_end < char_count:
            return None, None
        return index_start, index_end
    elif position_string == 'start':
        index_start = found[0].start()
        index_end = found[0].end()
        if index_start != 0:
            return None, None
        return index_start, index_end
    elif position_string == 'first':
        index_start = found[0].start()
        index_end = found[0].end()
        return index_start, index_end
    elif position_string == 'last':
        index_start = found[-1].start()
        index_end = found[-1].end()
        return index_start, index_end
    elif position_string == 'inside':
        for match in found:
            start_index = match.start()
            end_index = match.end()
            if start_index == 0:
                continue
            if end_index > char_count:
                continue
            break
        index_start = start_index
        index_end = end_index
        return index_start, index_end


def unix_match(pattern, name_list):
    """
    unix style matching that also matches Maya's name search.
    """
    matches = fnmatch.filter(name_list, pattern)
    return matches


def replace_string(string_value, replace_string, start, end):
    first_part = string_value[:start]
    second_part = string_value[end:]
    return first_part + replace_string + second_part


def replace_string_at_end(line, string_to_replace, replace_string):
    m = re.search('%s$' % string_to_replace, line)
    if not m:
        return

    start = m.start(0)
    end = m.end(0)

    new_line = line[:start] + replace_string + line[end:]

    return new_line


def replace_string_at_start(line, string_to_replace, replace_string):
    m = re.search('^%s' % string_to_replace, line)
    if not m:
        return

    start = m.start(0)
    end = m.end(0)

    new_line = line[:start] + replace_string + line[end:]

    return new_line


def clean_file_string(string):
    if not string:
        return
    if string == '/':
        return '_'
    string = string.replace('\\', '_')
    return string


def clean_name_string(string_value, clean_chars='_', remove_char='_'):
    string_value = re.sub('^[^A-Za-z0-9%s]+' % clean_chars, '', string_value)
    string_value = re.sub('[^A-Za-z0-9%s]+$' % clean_chars, '', string_value)
    string_value = re.sub('[^A-Za-z0-9]', remove_char, string_value)
    if not string_value:
        string_value = remove_char
    return string_value


def camel_to_underscore(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def remove_side(name):
    ending_cases = ['_L', '_R', '_l', '_r', '_lf', '_rt', '_C', '_c']
    starting_cases = ['L_', 'R_', 'l_', 'r_', 'lf_', 'rt_', 'C_', 'c_']
    anyplace_cases = ['Left', 'Right', 'left', 'right',
                      '_L_', '_R_', '_l_', '_r_',
                      '_lf_', '_rt_',
                      'Center', 'center',
                      '_C_', '_c_']

    # TODO: Investigate refactoring using find.
    for end_case in ending_cases:
        if name.endswith(end_case):
            return name[:-2], name[-1]

    # TODO: Investigate refactoring using find.
    for start_case in starting_cases:
        if name.startswith(start_case):
            return name[2:], name[0]

    for anyplace_case in anyplace_cases:
        find_index = name.find(anyplace_case)
        if find_index > -1:

            replace_string = ''

            if anyplace_case.startswith('_') and anyplace_case.endswith('_'):
                replace_string = '_'

            new_name = name[:find_index] + replace_string + name[find_index + len(anyplace_case):]
            side = anyplace_case.strip('_')

            if not replace_string:
                if new_name[find_index] == '_' and new_name[(find_index - 1)] == '_':
                    new_name = new_name[:(find_index - 1)] + '_' + new_name[(find_index + 1):]

            return new_name, side

    return name, None


def get_side_code(side_name):
    """
    given a side name like: Left,left,L,lf,l this will return L
    given a side name like: Right,right,R,rt,r this will return R
    given a side name like: Center,center,C,ct,c this will return C
    """

    if side_name.find('C') > -1 or side_name.find('c') > -1:
        return 'C'
    elif side_name.find('L') > -1 or side_name.find('l') > -1:
        return 'L'
    elif side_name.find('R') > -1 or side_name.find('r') > -1:
        return 'R'


#--- rigs
def is_left(side):
    return str(side) in ('L', 'l', 'Left', 'left', 'lf')


def is_right(side):
    return str(side) in ('R', 'r', 'Right', 'right', 'rt')


def is_center(side):
    return str(side) in ('C', 'c', 'Center', 'ct', 'center', 'middle', 'm')


def split_side_negative_number(name):
    last_number = get_trailing_number(name, as_string=True, number_count=2)

    negative = None
    side = None

    if last_number:
        name = name[:-2]

    if name.endswith('N'):
        negative = 'N'
        name = name[:-1]

    if name.endswith('L') or name.endswith('R'):
        side = name[-1]
        name = name[:-1]

    return name, side, negative, last_number


# TODO: Refactor Use itertools
def find_possible_combos(names, sort=False, one_increment=False):
    if not names:
        return []

    if sort:
        names.sort()

    if names:
        name_count = len(names)

        found = []

        if name_count > 1:

            for inc in range(0, name_count):
                next_inc = inc + 1

                if next_inc < name_count:

                    for inc2 in range(next_inc, name_count):
                        first_name = names[inc]
                        second_name = names[inc2]

                        if first_name == '%sN' % second_name:
                            continue

                        if second_name == '%sN' % first_name:
                            continue

                        name_combo = '_'.join([names[inc], names[inc2]])
                        found.append(name_combo)

                        sub_names = names[inc2:]

                        if len(sub_names) > 1:
                            found_sub_combos = find_possible_combos(names[inc2:], False, True)

                            for combo in found_sub_combos:
                                sub_name_combo = '_'.join([names[inc], combo])

                                found.append(sub_name_combo)

                if one_increment:
                    return found

            return found

#--- sorting


def sort_string_integer(list_of_strings):

    return sorted(list_of_strings, key=get_split_string_and_numbers)


def sort_data_by_numbers(data_list, number_list):
    """
    data_list and number_list need to be the same length
    """
    indexed_numbers = list(enumerate(number_list))
    indexed_numbers.sort(key=lambda x: x[1])
    sorted_strings = [data_list[i] for i, _ in indexed_numbers]

    return sorted_strings


def print_python_dir_nicely(python_object):
    stuff = dir(python_object)

    for thing in stuff:
        text = 'print( thing, ":", python_object.%s)' % thing
        exec(text)


def split_line(line, splitter=';', quote_symbol='"'):
    """
    This will split a line, ignoring anything inside quotes
    #re.split(';(?=(?:[^"]*"[^"]*")*[^"]*$)
    """

    split_regex = '%s(?=(?:[^%s]*%s[^%s]*%s)*[^%s]*$)' % (splitter,
                                                          quote_symbol,
                                                          quote_symbol,
                                                          quote_symbol,
                                                          quote_symbol,
                                                          quote_symbol)
    return re.split(split_regex, line)


def replace_vtool(path_to_vtool):
    """
    Meant to have vtool look at a different path to load
    """

    unload_vtool()
    sys.path.insert(0, path_to_vtool)


def remove_modules_at_path(path):
    show('Removing modules at path: %s' % path)

    modules_to_pop = []

    for key in sys.modules.keys():
        module = sys.modules[key]
        if not module:
            continue
        if hasattr(module, '__file__'):
            filepath = module.__file__
            filepath = filepath.replace('\\', '/')
            if filepath.startswith(path):
                modules_to_pop.append(key)

    for module in modules_to_pop:
        show('Removing module: %s' % module)
        sys.modules.pop(module)


def unload_vtool():
    """
    Removed currently sourced modules.
    This allows you to insert a custom path at the start of the sys.path and load vetala from there.
    """

    if in_maya:
        from vtool.maya_lib import ui_core
        ui_core.delete_scene_script_jobs()
        from vtool.maya_lib import api
        api.remove_check_after_save()

    modules = sys.modules

    found = []

    module_keys = modules.keys()

    for module in module_keys:

        if module not in modules:
            continue
        module_inst = modules[module]
        if not module_inst:
            continue
        if not hasattr(module_inst, '__file__'):
            continue
        if module.startswith('vtool'):
            found.append(module)

    for key in found:
        show('Removing vtool module %s' % key)
        modules.pop(key)


def get_square_bracket_numbers(input_string):
    match = re.findall('(?<=\[)[0-9]*', input_string)
    if not match:
        return
    found = []
    for thing in match:
        found.append(eval(thing))
    return found


def scale_dpi(float_value):

    scale = 1

    if in_houdini:
        scale = hou.ui.globalScaleFactor()
        scale *= 1.8
    elif in_maya:
        if is_windows() or is_linux():
            scale = cmds.mayaDpiSetting(rsv=True, q=True)
    else:
        scale = 1

        from . import qt
        app = qt.QApplication.instance()
        screen = app.primaryScreen()
        logical_dpi = screen.logicalDotsPerInch()

        scale = logical_dpi * .01
        scale *= 1.25

    return float_value * scale


def convert_text_for_sorting(text):

    parts = []
    for section in text.split('.'):
        split_parts = [int(p) if p.isdigit() else p.lower() for p in re.split(r'(\d+)', section) if p]
        if len(split_parts) == 1:
            split_parts.append(0)
        parts.extend(split_parts)
    return parts


def sort_function_number(item):
    match = re.match(r'(\D*)(\d+)', item)
    if match:
        prefix = match.group(1)
        number = int(match.group(2))
        return prefix, number
    else:
        return item


def compare_dict(dict1, dict2):

    if dict1.keys() != dict2.keys():
        return False

    for key in dict1.keys():

        if type(dict1.get(key)) == dict:
            if not type(dict2.get(key)) == dict:
                return False
            compare = compare_dict(dict1.get(key), dict2.get(key))

            if not compare:
                return False

        elif dict1.get(key) != dict2.get(key):
            return False

    return True


def copy_to_clipboard(text):

    if is_windows():
        subprocess.run("clip", input=text.encode("utf-16"), check=True, creationflags=subprocess.CREATE_NO_WINDOW)
    elif is_linux():
        subprocess.run("xclip -selection clipboard", input=text.encode(), check=True, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        raise NotImplementedError("Clipboard copy not supported.")
