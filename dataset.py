import bpy, bmesh
from datetime import datetime
from math import ceil, radians
import numpy as np
import os
import random
import sys
from time import time

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)

from annotation import Annotation
from blender_utils import extrude, gancio, get_min_max
from cameramanager import CameraManager
from dataset_config import *
from generator import BuildingFactory
from light import LightManager
from material import MaterialFactory
from module import *
from point_cloud import PointCloud
from renderer import Renderer
from shp2obj import Collection, deselect_all


class Dataset:
	"""
	Class that manages and creates the dataset.
	"""
	def __init__(self):
		"""
		Class initialization.
		"""
		self.name = 'Building_dataset_{}_{}_{}'.format(datetime.now().year,
		                                               datetime.now().month,
		                                               datetime.now().day)
		self.size = SIZE
		self.json = Annotation()
		self.factory = BuildingFactory()
		self.material_factory = MaterialFactory()

	def populate(self):
		"""
		Function that creates the dataset samples.
		:return:
		"""
		s = time()
		renderer = Renderer(mode=0)
		lightmanager = LightManager()
		cameramanager = CameraManager()
		for i in range(self.size):
			lightmanager.make()
			building = self.factory.produce()
			building.make()
			if use_materials:
				_monomaterial = np.random.random() < MATERIAL_PROB
				mat = self.material_factory.produce()
				for v in building.volumes:
					if not _monomaterial:
						mat = self.material_factory.produce()
					v.apply(mat)
					v.add_modules()

			self.json.add(building, '{}.png'.format(i), '{}.obj'.format(i))
			cameramanager.make_main()
			renderer.render(filename='building_{}'.format(i))
			if RENDER_VIEWS > 1:
				for view in range(1, RENDER_VIEWS):
					cameramanager.make()
					lightmanager.make()
					if RANDOMIZE_TEXTURES:
						if use_materials:
							_monomaterial = np.random.random() < MATERIAL_PROB
							mat = self.material_factory.produce()
							for v in building.volumes:
								if not _monomaterial:
									mat = self.material_factory.produce()
								v.apply(mat)

					renderer.render(filename='building_{}_{}'.format(i, view))
			building.save(i)
			building.save(i, ext='ply')
			if BLEND_SAVE:
				building.save(i, ext='blend')
			building.demolish()
			cloud = PointCloud()
			cloud.make(i)


		print('Whole process took: {}'.format(time() - s))

	def write(self):
		"""
		Function that writes a json annotation to the dataset.
		:return:
		"""
		self.json.write(self.name + '.json')


if __name__ == '__main__':
	d = Dataset()
	d.populate()
	d.write()


