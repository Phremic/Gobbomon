import os
import shutil
import json

content_mods = []
dependency_mods = []
enabled_mods = []
unused_mods = []


def log_info(info_data):
    print('[INFO]', info_data)


# Get the project directory
PROGRAM_FILEPATH = '\\0 - Python\\generate_instance.py'
if PROGRAM_FILEPATH not in __file__:
    raise RuntimeError('Program file not in expected directory')
PROJECT_DIRECTORY = __file__.replace(PROGRAM_FILEPATH, '')

# Get the project name
PROJECT_NAME = os.path.basename(PROJECT_DIRECTORY)
log_info('Project name: ' + PROJECT_NAME)

# Get the root directory (Should be the ATLauncher install location)
DEVELOPMENT_FILEPATH = os.path.dirname(PROJECT_DIRECTORY)
ROOT_DIRECTORY = os.path.dirname(DEVELOPMENT_FILEPATH)
log_info('Root directory: ' + ROOT_DIRECTORY)

# Create a clean instance directory
INSTANCE_DIRECTORY = ROOT_DIRECTORY + '\\instances\\' + PROJECT_NAME
if os.path.exists(INSTANCE_DIRECTORY):
    shutil.rmtree(INSTANCE_DIRECTORY)
os.makedirs(INSTANCE_DIRECTORY)

# Copy core files to instance directory
INSTANCE_CORE_DIRECTORY = PROJECT_DIRECTORY + '\\1 - Instance Core'
shutil.copytree(INSTANCE_CORE_DIRECTORY, INSTANCE_DIRECTORY, dirs_exist_ok=True)
core_changelog_filepath = INSTANCE_DIRECTORY + '\\config\\_changelog.txt'
if os.path.isfile(core_changelog_filepath):
    os.remove(core_changelog_filepath)
log_info('Added core instance files')

# Generate mod lists
CONTENT_MODS_DIRECTORY = PROJECT_DIRECTORY + '\\3 - Content Mods\\Enabled'
content_mods = [f.name for f in os.scandir(CONTENT_MODS_DIRECTORY) if f.is_dir()]
DEPENDENCY_MODS_DIRECTORY = PROJECT_DIRECTORY + '\\4 - Dependency Mods'
dependency_mods = [f.name for f in os.scandir(DEPENDENCY_MODS_DIRECTORY) if f.is_dir()]
unused_mods = dependency_mods + content_mods


# ---------------- ADD MODS ----------------

def add_mod_to_instance(mod_directory, mod_name):
    if mod_name in enabled_mods:
        return

    data_directory = mod_directory + '\\' + mod_name
    data_filepath = data_directory + '\\data.json'
    with open(data_filepath, 'r') as file:
        data = json.load(file)

    if not data['Client']:
        return

    for dependency_mod in data['Dependencies']:
        if dependency_mod in content_mods:
            add_mod_to_instance(CONTENT_MODS_DIRECTORY, dependency_mod)
        elif dependency_mod in dependency_mods:
            add_mod_to_instance(DEPENDENCY_MODS_DIRECTORY, dependency_mod)
        else:
            raise RuntimeError('Required mod \"' + dependency_mod + '\" is missing from project mods')

    for f in os.scandir(data_directory):
        if f.is_dir():
            shutil.copytree(data_directory + '\\' + f.name, INSTANCE_DIRECTORY + '\\' + f.name, dirs_exist_ok=True)
            if f.name == 'config':
                changelog_filepath = INSTANCE_DIRECTORY + '\\config\\_changelog.txt'
                if os.path.isfile(changelog_filepath):
                    os.remove(changelog_filepath)

    enabled_mods.append(mod_name)
    unused_mods.remove(mod_name)
    log_info('Added mod: ' + mod_name)


for mod in content_mods:
    add_mod_to_instance(CONTENT_MODS_DIRECTORY, mod)


# ---------------- ADD RESOURCE PACKS ----------------

RESOURCE_PACKS_DIRECTORY = PROJECT_DIRECTORY + '\\5 - Resource Packs'
shutil.copytree(RESOURCE_PACKS_DIRECTORY, INSTANCE_DIRECTORY + '\\resourcepacks', dirs_exist_ok=True)
log_info('Added resource pack files ')


# ---------------- ADD SHADER PACKS ----------------

SHADER_PACKS_DIRECTORY = PROJECT_DIRECTORY + '\\6 - Shader Packs'
shutil.copytree(SHADER_PACKS_DIRECTORY, INSTANCE_DIRECTORY + '\\shaderpacks', dirs_exist_ok=True)
log_info('Added shader pack files ')

if len(unused_mods) > 0:
    print()
    print('[WARNING] The following dependency mods included in the project are not required')
    print(unused_mods)
