import os
import shutil
import functions


# ---------------- FIND PROJECT DIRECTORY ----------------

# Get the project directory
PROGRAM_FILEPATH = '\\0 - Python\\generate_server.py'
if PROGRAM_FILEPATH not in __file__:
    raise RuntimeError('Program file not in expected directory')
PROJECT_DIRECTORY = __file__.replace(PROGRAM_FILEPATH, '')
functions.log_info('Project directory: ' + PROJECT_DIRECTORY)

# Get the project name
PROJECT_NAME = os.path.basename(PROJECT_DIRECTORY)
functions.log_info('Project name: ' + PROJECT_NAME)

# ---------------- FIND ATLAUNCHER DIRECTORY ----------------

ATLAUNCHER_DIRECTORY = functions.locate_atlauncher_directory(os.path.join(os.path.dirname(__file__), 'data.json'))
functions.log_info('ATLauncher install directory: ' + ATLAUNCHER_DIRECTORY)

# Create a clean instance directory
SERVERS_DIRECTORY = str(os.path.join(ATLAUNCHER_DIRECTORY, 'servers', PROJECT_NAME))
if os.path.exists(SERVERS_DIRECTORY):
    shutil.rmtree(SERVERS_DIRECTORY)
    functions.log_info('Removed existing servers directory')
os.makedirs(SERVERS_DIRECTORY)
functions.log_info('ATLauncher servers directory: ' + SERVERS_DIRECTORY)

# ---------------- ADD CORE FILES ----------------

# Copy core files to server directory
shutil.copytree(os.path.join(PROJECT_DIRECTORY, '2 - Server Core'), SERVERS_DIRECTORY, dirs_exist_ok=True)
functions.log_info('Added core server files')

# Remove server core config changelog file from new server
core_changelog_filepath = os.path.join(SERVERS_DIRECTORY, 'config', '_changelog.txt')
if os.path.isfile(core_changelog_filepath):
    os.remove(core_changelog_filepath)
    functions.log_info('Removed forge mod loader changelog file from server')

# ---------------- ADD MODS ----------------

enabled_mods = []

for mod in os.scandir(os.path.join(PROJECT_DIRECTORY, '3 - Content Mods', 'Enabled')):
    if mod.is_dir():
        enabled_mods.extend(functions.add_mod(mod.name, enabled_mods, PROJECT_DIRECTORY, SERVERS_DIRECTORY))

functions.log_info('Total mods added: ' + str(len(enabled_mods)))

# ---------------- SHOW UNUSED MODS ----------------

unused_mods = [mod.name for mod in os.scandir(os.path.join(PROJECT_DIRECTORY, '4 - Dependency Mods')) if mod.is_dir() and mod.name not in enabled_mods]
if len(unused_mods) > 0:
    print()
    print('[WARNING] The following dependency mods included in the project are not required')
    print(unused_mods)
