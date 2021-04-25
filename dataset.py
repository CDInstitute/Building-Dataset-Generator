import bpy, bmesh
from datetime import datetime
from math import ceil, radians
import numpy as np
import os
import random
import sys

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)

from annotation import Annotation
from blender_utils import extrude, gancio, get_min_max
from dataset_config import *
from generator import BuildingFactory
from material import MaterialFactory
from module import *
from point_cloud import PointCloud
from renderer import Renderer
from shp2obj import Collection, deselect_all


class Dataset:
	def __init__(self):
		self.name = 'Building_dataset_{}_{}_{}'.format(datetime.now().year,
		                                               datetime.now().month,
		                                               datetime.now().day)
		self.size = SIZE
		self.json = Annotation()
		self.factory = BuildingFactory()
		self.material_factory = MaterialFactory()

	def populate(self):
		for i in range(self.size):
			building = self.factory.produce()
			building.make()
			if use_materials:
				_monomaterial = np.random.random() < MATERIAL_PROB
				mat = self.material_factory.produce()
				print(mat.name)
				for v in building.volumes:
					if not _monomaterial:
						mat = self.material_factory.produce()
					v.apply(mat)

					for module_name in MODULES:
						for side in range(2):
							mod = GridApplier(ModuleFactory().mapping[module_name])
							module = ModuleFactory().produce(module_name)
							module.connect(v, side)
							step = (np.random.randint(ceil(module.scale[0]), 6),
							        np.random.randint(ceil(module.scale[0]), 6))
							mod.apply(module, step=step, offset=(2.0, 2.0, 2.0, 1.0))

			self.json.add(building, '{}.png'.format(i), '{}.obj'.format(i))
			# building.save(filename=str(i))
			renderer = Renderer(mode=0)
			renderer.render(filename='building_{}'.format(i))
			building.save(i)
			building.save(i, ext='ply')
			building.demolish()
			cloud = PointCloud()
			cloud.make(i)


	def write(self):
		self.json.write(self.name + '.json')


if __name__ == '__main__':
	d = Dataset()
	d.populate()
	d.write()


