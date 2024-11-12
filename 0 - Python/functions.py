import json
import os
import shutil
import string

ATLAUNCHER_FILENAME = 'ATLauncher.exe'


def log_info(info_data):
    print('[INFO]', info_data)


def log_warning(warning_data):
    print('[WARNING]', warning_data)


def get_project_directory():
    return os.path.dirname(os.path.dirname(__file__))


def locate_atlauncher_directory():

    directory = ''
    data_filepath = os.path.join(os.path.dirname(__file__), 'data.json')

    try:
        with open(data_filepath, 'r') as data:
            directory = json.load(data).get('Install Directory')
    except FileNotFoundError:
        log_warning('Unable to find ATLauncher install directory data file')
    except json.JSONDecodeError:
        log_warning('Unable to read ATLauncher install directory data file')
    finally:
        if directory is None:
            log_warning('ATLauncher install directory data file doesn\'t contain directory data')
        elif not isinstance(directory, str):
            log_warning('ATLauncher install directory data contains an invalid datatype')
        elif len(directory) == 0:
            log_warning('ATLauncher install directory data doesn\'t contain a valid directory')
        elif not os.path.isfile(os.path.join(directory, ATLAUNCHER_FILENAME)):
            log_warning('ATLauncher install directory data doesn\'t contain a valid file')
        else:
            return directory

    log_info('Searching for ATLauncher install directory...')
    for letter in string.ascii_uppercase:
        for root, dirs, files in os.walk(letter + ':\\'):
            if ATLAUNCHER_FILENAME in files:
                log_info('Found ATLauncher install at the following location: ' + root)
                while True:
                    match input('Would you like to use this as your ATLauncher install directory? (y/n) '):
                        case 'y' | 'Y':
                            with open(data_filepath, "w") as data:
                                data.write(json.dumps({'Install Directory': root}, indent=4))
                            log_info('Stored ATLauncher install directory in data file')
                            return root
                        case 'n' | 'N':
                            break
                        case _:
                            print('INVALID RESPONSE')
    raise RuntimeError('Unable to load ATLauncher install directory')


def remove_changelog(directory, sub_directory):

    # Remove a changelog file if one exists
    changelog_filepath = os.path.join(directory, sub_directory, '_changelog.txt')
    if os.path.isfile(changelog_filepath):
        os.remove(changelog_filepath)


def generate_instance_directory(instance_type):

    # Get the ATLauncher install directory
    atlauncher_directory = locate_atlauncher_directory()
    log_info('ATLauncher install directory: ' + atlauncher_directory)

    # Get the instance directory
    instance_directory = str(os.path.join(atlauncher_directory, instance_type, os.path.basename(get_project_directory())))

    # Remove an existing instance directory if one exist
    if os.path.exists(instance_directory):
        shutil.rmtree(instance_directory)
        log_info('Removed existing ' + instance_type + ' directory')

    # Make a new instance directory
    os.makedirs(instance_directory)
    log_info('ATLauncher ' + instance_type + ' directory: ' + instance_directory)

    return instance_directory


def add_core_files(instance_directory, core_type):

    # Copy core files to instance directory
    shutil.copytree(
        os.path.join(get_project_directory(), str(core_type)),
        instance_directory,
        dirs_exist_ok=True)
    log_info('Added core files')

    # Remove instance core config changelog file from new instance
    remove_changelog(instance_directory, 'config')
    remove_changelog(instance_directory, 'defaultconfigs')


def get_mod_directory(f_mod_name, f_project_directory):

    # Check if the mod exists in the content mods directory
    for mod in os.scandir(os.path.join(f_project_directory, '3 - Content Mods', 'Enabled')):
        if mod.is_dir() and mod.name == f_mod_name:
            return mod.path

    # Check if the mod exists in the dependency mods directory
    for mod in os.scandir(os.path.join(f_project_directory, '4 - Dependency Mods')):
        if mod.is_dir() and mod.name == f_mod_name:
            return mod.path

    # Raise error if the mod could not be found
    raise RuntimeError('Required mod \"' + f_mod_name + '\" is missing from project')


def add_mod(f_mod_name, f_enabled_mods, f_target_directory):

    added_mods = []

    # Check if mod has already been added
    if f_mod_name in f_enabled_mods:
        return added_mods

    # Get the mod directory and open the mod data file
    mod_directory = get_mod_directory(f_mod_name, get_project_directory())
    with open(os.path.join(mod_directory, 'data.json'), 'r') as data:

        # Load mod data file
        mod_data = json.load(data)

        # Prevent a non client side mod from being added to the client
        if not mod_data['Client']:
            if os.path.basename(os.path.dirname(f_target_directory)) == 'instances':
                return added_mods

        # Prevent a non server side mod from being added to the server
        if not mod_data['Server']:
            if os.path.basename(os.path.dirname(f_target_directory)) == 'servers':
                return added_mods

        # Add dependency mods if required
        for dependency_mod in mod_data['Dependencies']:
            if dependency_mod not in added_mods:
                added_mods.extend(add_mod(dependency_mod, f_enabled_mods, f_target_directory))
                if dependency_mod not in added_mods:
                    if dependency_mod not in f_enabled_mods:
                        raise RuntimeError('Required mod \"' + dependency_mod + '\" was unable to be added')

        # Add all mod files
        for f in os.scandir(mod_directory):
            if f.is_dir():
                if f.name == 'config' or f.name == 'defaultconfigs':
                    if not os.path.isfile(os.path.join(mod_directory, f.name, '_changelog.txt')):
                        continue
                shutil.copytree(
                    os.path.join(mod_directory, f.name),
                    os.path.join(f_target_directory, f.name),
                    dirs_exist_ok=True)

        # Remove config changelog file
        remove_changelog(f_target_directory, 'config')
        remove_changelog(f_target_directory, 'defaultconfigs')

    # Return list of all mods that have been added from this function call and recursive calls
    log_info('Added mod: ' + f_mod_name)
    added_mods.append(f_mod_name)
    return added_mods


def add_mods(instance_directory):
    enabled_mods = []
    for mod in os.scandir(os.path.join(get_project_directory(), '3 - Content Mods', 'Enabled')):
        if mod.is_dir():
            enabled_mods.extend(add_mod(mod.name, enabled_mods, instance_directory))
    log_info('Total mods added: ' + str(len(enabled_mods)))

    return [mod.name for mod in os.scandir(os.path.join(get_project_directory(), '4 - Dependency Mods')) if mod.is_dir() and mod.name not in enabled_mods]


def add_resource_packs(instance_directory):
    shutil.copytree(
        os.path.join(get_project_directory(), '5 - Resource Packs'),
        os.path.join(instance_directory, 'resourcepacks'),
        dirs_exist_ok=True)
    log_info('Added resource pack files')


def add_shader_packs(instance_directory):
    shutil.copytree(
        os.path.join(get_project_directory(), '6 - Shader Packs'),
        os.path.join(instance_directory, 'shaderpacks'),
        dirs_exist_ok=True)
    log_info('Added shader pack files')
