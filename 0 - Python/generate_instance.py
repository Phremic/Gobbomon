import json
import os
import shutil
import string

enabled_mods = []
unused_mods = []


def log_info(info_data):
    print('[INFO]', info_data)


def log_warning(warning_data):
    print('[WARNING]', warning_data)


def locate_atlauncher_directory(data_filepath):
    try:
        with open(data_filepath, 'r') as data:
            return json.load(data)['Install Directory']
    except FileNotFoundError:
        log_warning('Unable to find ATLauncher install directory data file')
    except json.JSONDecodeError:
        log_warning('Unable to read ATLauncher install directory data file')
    finally:
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


def add_mod_to_instance(f_mod_name, f_project_directory, f_instances_directory):
    if f_mod_name in enabled_mods:
        return

    content_mods_directory = os.path.join(f_project_directory, '3 - Content Mods', 'Enabled')
    content_mods = [f.name for f in os.scandir(content_mods_directory) if f.is_dir()]

    dependency_mods_directory = os.path.join(f_project_directory, '4 - Dependency Mods')
    dependency_mods = [f.name for f in os.scandir(dependency_mods_directory) if f.is_dir()]

    if f_mod_name in content_mods:
        mod_directory = os.path.join(content_mods_directory, f_mod_name)
    elif f_mod_name in dependency_mods:
        mod_directory = os.path.join(dependency_mods_directory, f_mod_name)
    else:
        raise RuntimeError('Required mod \"' + f_mod_name + '\" is missing from project')

    with open(os.path.join(mod_directory, 'data.json'), 'r') as data:
        data = json.load(data)

        if not data['Client']:
            return

        for dependency_mod in data['Dependencies']:
            add_mod_to_instance(dependency_mod, f_project_directory, f_instances_directory)

        for f in os.scandir(mod_directory):
            if f.is_dir():
                shutil.copytree(
                    os.path.join(mod_directory, f.name),
                    os.path.join(f_instances_directory, f.name),
                    dirs_exist_ok=True)
                if f.name == 'config':
                    changelog_filepath = os.path.join(f_instances_directory, f.name, '_changelog.txt')
                    if os.path.isfile(changelog_filepath):
                        os.remove(changelog_filepath)

    enabled_mods.append(f_mod_name)
    log_info('Added mod: ' + f_mod_name)


# ---------------- FIND PROJECT DIRECTORY ----------------

# Get the project directory
PROGRAM_FILEPATH = '\\0 - Python\\generate_instance.py'
if PROGRAM_FILEPATH not in __file__:
    raise RuntimeError('Program file not in expected directory')
PROJECT_DIRECTORY = __file__.replace(PROGRAM_FILEPATH, '')
log_info('Project directory: ' + PROJECT_DIRECTORY)

# Get the project name
PROJECT_NAME = os.path.basename(PROJECT_DIRECTORY)
log_info('Project name: ' + PROJECT_NAME)

# ---------------- FIND ATLAUNCHER DIRECTORY ----------------

ATLAUNCHER_FILENAME = 'ATLauncher.exe'

ATLAUNCHER_DIRECTORY = locate_atlauncher_directory(os.path.join(os.path.dirname(__file__), 'data.json'))
log_info('ATLauncher install directory: ' + ATLAUNCHER_DIRECTORY)

# Create a clean instance directory
INSTANCES_DIRECTORY = str(os.path.join(ATLAUNCHER_DIRECTORY, 'instances', PROJECT_NAME))
if os.path.exists(INSTANCES_DIRECTORY):
    shutil.rmtree(INSTANCES_DIRECTORY)
    log_info('Removed existing instances directory')
os.makedirs(INSTANCES_DIRECTORY)
log_info('ATLauncher instances directory: ' + INSTANCES_DIRECTORY)

# ---------------- ADD CORE FILES ----------------

# Copy core files to instance directory
shutil.copytree(os.path.join(PROJECT_DIRECTORY, '1 - Instance Core'), INSTANCES_DIRECTORY, dirs_exist_ok=True)
log_info('Added core instance files')

# Remove instance core config changelog file from new instance
core_changelog_filepath = os.path.join(INSTANCES_DIRECTORY, 'config', '_changelog.txt')
if os.path.isfile(core_changelog_filepath):
    os.remove(core_changelog_filepath)
    log_info('Removed forge mod loader changelog file from instance')

# ---------------- ADD MODS ----------------

# Generate mod lists
CONTENT_MODS_DIRECTORY = str(os.path.join(PROJECT_DIRECTORY, '3 - Content Mods', 'Enabled'))
CONTENT_MODS = [f.name for f in os.scandir(CONTENT_MODS_DIRECTORY) if f.is_dir()]

DEPENDENCY_MODS_DIRECTORY = os.path.join(PROJECT_DIRECTORY, '4 - Dependency Mods')
DEPENDENCY_MODS = [f.name for f in os.scandir(DEPENDENCY_MODS_DIRECTORY) if f.is_dir()]

for mod_name in CONTENT_MODS:
    add_mod_to_instance(mod_name, PROJECT_DIRECTORY, INSTANCES_DIRECTORY)

log_info('Total mods added: ' + str(len(enabled_mods)))

# ---------------- ADD RESOURCE PACKS ----------------

shutil.copytree(
    os.path.join(PROJECT_DIRECTORY, '5 - Resource Packs'),
    os.path.join(INSTANCES_DIRECTORY, 'resourcepacks'),
    dirs_exist_ok=True)
log_info('Added resource pack files')

# ---------------- ADD SHADER PACKS ----------------

shutil.copytree(
    os.path.join(PROJECT_DIRECTORY, '6 - Shader Packs'),
    os.path.join(INSTANCES_DIRECTORY, 'shaderpacks'),
    dirs_exist_ok=True)
log_info('Added shader pack files')

# ---------------- SHOW UNUSED MODS ----------------

unused_mods = [item for item in CONTENT_MODS + DEPENDENCY_MODS if item not in enabled_mods]
if len(unused_mods) > 0:
    print()
    print('[WARNING] The following dependency mods included in the project are not required')
    print(unused_mods)
