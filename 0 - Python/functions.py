import json
import os
import shutil
import string


ATLAUNCHER_FILENAME = 'ATLauncher.exe'


def log_info(info_data):
    print('[INFO]', info_data)


def log_warning(warning_data):
    print('[WARNING]', warning_data)


def locate_atlauncher_directory(data_filepath):

    directory = ''

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


def get_mod_directory(f_mod_name, f_project_directory):

    for mod in os.scandir(os.path.join(f_project_directory, '3 - Content Mods', 'Enabled')):
        if mod.is_dir() and mod.name == f_mod_name:
            return mod.path

    for mod in os.scandir(os.path.join(f_project_directory, '4 - Dependency Mods')):
        if mod.is_dir() and mod.name == f_mod_name:
            return mod.path

    raise RuntimeError('Required mod \"' + f_mod_name + '\" is missing from project')


def add_mod(f_mod_name, f_enabled_mods, f_project_directory, f_target_directory):

    added_mods = []

    # Check if mod has already been added
    if f_mod_name in f_enabled_mods:
        return added_mods

    # Get the mod directory and open the mod data file
    mod_directory = get_mod_directory(f_mod_name, f_project_directory)
    with open(os.path.join(mod_directory, 'data.json'), 'r') as data:

        # Load mod data file
        mod_data = json.load(data)

        if not mod_data['Client']:
            if os.path.basename(os.path.dirname(f_target_directory)) == 'instances':
                return added_mods

        if not mod_data['Server']:
            if os.path.basename(os.path.dirname(f_target_directory)) == 'servers':
                return added_mods

        # Add dependency mods if required
        for dependency_mod in mod_data['Dependencies']:
            added_mods.extend(add_mod(dependency_mod, f_enabled_mods, f_project_directory, f_target_directory))
            if dependency_mod not in added_mods:
                if dependency_mod not in f_enabled_mods:
                    raise RuntimeError('Required mod \"' + dependency_mod + '\" was unable to be added')

        for f in os.scandir(mod_directory):
            if f.is_dir():
                if f.name == 'config':
                    changelog_filepath = os.path.join(mod_directory, f.name, '_changelog.txt')
                    if not os.path.isfile(changelog_filepath):
                        continue
                shutil.copytree(
                    os.path.join(mod_directory, f.name),
                    os.path.join(f_target_directory, f.name),
                    dirs_exist_ok=True)

        changelog_filepath = os.path.join(f_target_directory, 'config', '_changelog.txt')
        if os.path.isfile(changelog_filepath):
            os.remove(changelog_filepath)

    log_info('Added mod: ' + f_mod_name)
    added_mods.append(f_mod_name)
    return added_mods
