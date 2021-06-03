MIN_HEIGHT = 3.0
MIN_WIDTH = 6.0
MIN_LENGTH = 6.0

MAX_HEIGHT = 30.0
MAX_WIDTH = 30.0
MAX_LENGTH = 30.0

MAX_VOLUMES = 4

# BUILDINGS = ['Patio', 'L', 'C', 'Single', 'Skyscraper', 'Closedpatio', 'Equalpatio']
# Choose building typologies to be produced
BUILDINGS = ['Patio', 'L', 'C', 'Single', 'Closedpatio', 'Equalpatio'] # , 'Skyscraper']

SIZE = 2  # dataset size

use_materials = True  # apply materials to the facades of the buildings, bool

MATERIAL_PROB = 0.7  # Probability of all the volumes of one building to be of the same material

use_modules = True

MODULES = {'window': {'rule': 'grid',
                      'materials': ['glass']},  # variant: material
           'balcony': {'rule': 'column',
                       'materials': []  # if material None - get random from the existing ones, if 0 - as .mtl file
                       },
           'roof': {'rule': 'single',
                    'materials': ['metall']}

            }  # grid, single, row, column, random


POINTS = 2048  # points to be samples from the mesh to get a point cloud
# 2048 in ModelNET

RENDER_EXR = False  # change for True if you want an .exr depth map

RANDOMIZE_TEXTURES = False  # randomization of textures per every additional view

RENDER_VIEWS = 2

IMAGE_SIZE = (500, 500)
MODEL_SAVE = 'Models'
IMG_SAVE = 'Images'
MASK_SAVE = 'Masks'
CLOUD_SAVE = 'PointCloud'
DEPTH_SAVE = 'Depth'
MODULE_PATH = 'Modules'
NORMALS_SAVE = 'Normals'

ENGINE = 'CYCLES'

SCRIPT_PATH = open('setup.txt').read()[:-1]