# cmddir

A prototype Directory Structure based Menu generating system

This supports walking a Directory that has inner subfolder + bash/python scripts and generates:

1. A custom Bullet based Menu System for each Subdirectory Tree
2. Sensible default shortcuts for each item (configurable by placing a config.json file in the associated subdir)
3. Configurable (as mentioned above)
4. Smart imports from an associated extern custom Python Module or the Directory structure itself can be a Pythonesque module structure
   1. for use in Leaf commands defiend as a .py script

More readme goes here

# NOTE: Python 3.10+ only

Since I've been using 3.10+ features, this is only supported with the latest 3.10+ python
