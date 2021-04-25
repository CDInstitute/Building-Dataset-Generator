import bpy, bmesh
from math import radians
import numpy as np
import os

import random
import sys

sys.path.append("D:\ProgramFiles\Anaconda\envs\py37\Lib\site-packages")
from pyntcloud import PyntCloud

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)

from blender_utils import extrude, gancio, get_min_max
from dataset_config import *
from material import Material
from module import *
from point_cloud import PointCloud
from renderer import Renderer
from shp2obj import Collection, deselect_all
from volume import *


class BuildingFactory:
	"""
	Factory that produces volumes.
	"""
	def __init__(self):

		self.mapping = {'Patio': (Patio, 4),
			            'L': (LBuilding, 2),
			            'C': (CBuilding, 3),
			            'Single': (ComposedBuilding, 1),
			            'Skyscraper': (Skyscraper, 1),
			            'Closedpatio': (ClosedPatio, 2),
			            'Equalpatio': (PatioEqual, 4)}
		self.mapping = {x: y for x, y in self.mapping.items() if x in BUILDINGS}

	def produce(self, name=None):
		"""
		Function that produces a volume based on the given scale.
		:param scale: tuple (width, length, height)
		:return: generated volume, Volume
		"""
		if name:
			name = name.lower().capitalize()
			assert name in list(self.mapping.keys()), "{} building typology " \
			                                          "does not exist".format(name)
		else:
			name = np.random.choice(list(self.mapping.keys()))
		_volumes = CollectionFactory().produce(number=self.mapping[name][1]).collection
		return self.mapping[name][0](_volumes)


class ComposedBuilding:
	"""
	Class that represents a building composed of one or several volumes.
	"""
	def __init__(self, volumes):
		assert isinstance(volumes, list), "Expected volumes as list," \
		                                  " got {}".format(type(volumes))
		self.volumes = volumes

	# def demolish(self):
	# 	for v in self.volumes:
	# 		try:
	# 			deselect_all()
	# 			v.mesh.select_set(True)
	# 			bpy.ops.object.delete()
	# 		except Exception:
	# 			pass

	def demolish(self):
		for _mesh in bpy.data.collections['Building'].objects:
			try:
				deselect_all()
				_mesh.select_set(True)
				bpy.ops.object.delete()
			except Exception:
				pass

	def get_bb(self):
		"""
		Function that gets the bounding box of the Building
		:return: bounding box, list of float
		[width_from, height_from, width_to, height_to]
		"""
		x_min, y_min, x_max, y_max = list(get_min_max(self.volumes[0].mesh, 0)) + \
		                             list(get_min_max(self.volumes[0].mesh, 1))
		for v in self.volumes[1:]:
			_bb = list(get_min_max(v.mesh, 0)) + \
			      list(get_min_max(v.mesh, 1))
			x_min, y_min = min(_bb[0], x_min), min(_bb[1], y_min)
			x_max, y_max = max(_bb[2], x_max), max(_bb[3], y_max)
		return [round(x_min, 3), round(y_min, 3), round(x_max, 3),
		        round(y_max, 3)]

	def make(self):
		"""
		Function that composes the building based on its typology.
		:return:
		"""
		self._correct_volumes()
		return self.volumes

	def save(self, filename='test', ext='obj'):
		"""
		Function that saves the building as a separate file.
		:param filename: name of the file to write without extension, str,
		default='test'
		:param ext: file extension, str, default='obj'
		:return:
		"""
		deselect_all()
		for v in self.volumes:
			v.mesh.select_set(True)
		if not MODEL_SAVE in os.listdir(file_dir):
			os.mkdir(file_dir + '/' + MODEL_SAVE)
		if ext == 'obj':
			bpy.ops.export_scene.obj(filepath='{}/Models/{}.{}'.format(file_dir,
			                                                           filename,
			                                                           ext),
			                         use_selection=False)
		elif ext == 'ply':
			bpy.ops.export_mesh.ply(
				filepath='{}/{}/{}.{}'.format(file_dir, CLOUD_SAVE, filename, ext),
				use_selection=False)
		else:
			return NotImplementedError

	def _correct_volumes(self):
		for v in self.volumes:
			v.create()


class LBuilding(ComposedBuilding):
	"""
	Class that represents an L-shaped building.
	"""
	def __init__(self, volumes):
		ComposedBuilding.__init__(self, volumes)

	def make(self):
		# add rotation if len > width (or vice versa)
		self._correct_volumes()
		gancio(self.volumes[0], self.volumes[1], 0, 0, 0)
		return self.volumes

	def _correct_volumes(self):

		if np.random.random() < 0.5:  # same height
			_height = max(min(self.volumes[0].height,
			                  min(self.volumes[0].width * 3, MAX_HEIGHT)),
			              MIN_HEIGHT)
			for v in self.volumes:
				v.height = _height

		for v in self.volumes:
			v.create()
		self.volumes = sorted(self.volumes, key=lambda x: x.length,
		                      reverse=True)


class CBuilding(LBuilding):
	def __init__(self, volumes):
		LBuilding.__init__(self, volumes)
		assert len(
			volumes) == 3, "C-shaped bulding can be composed of 3 volumes" \
		                   "only, got {}".format(len(volumes))

	def make(self):
		self._correct_volumes()
		for v in self.volumes[1:]:
			if v.width < v.length:
				v.mesh.rotation_euler[2] = radians(90)

		gancio(self.volumes[0], self.volumes[1], 0, 1, 0)
		gancio(self.volumes[0], self.volumes[2], 0, 0, 0)
		return self.volumes


class Patio(ComposedBuilding):
	"""
	Class that represents an L-shaped building.
	"""
	def __init__(self, volumes):
		ComposedBuilding.__init__(self, volumes)
		assert len(volumes) in [2, 4], "Patio bulding can be composed of 4 " \
		                               "volumes only, got {}".format(len(volumes))
		self.width = [3, 12]
		self.length = [6, 20]

	def make(self):

		self._correct_volumes()
		if np.random.random() < 0.5:
			# circular linkage between buildings
			for i, _v in enumerate(self.volumes[:-1]):
				if i % 2 == 0:
					self.volumes[i + 1].mesh.rotation_euler[2] = radians(90)
				if i == 0:
					gancio(_v, self.volumes[i + 1], 0, 1, 1)
				elif i == 1:
					gancio(_v, self.volumes[i + 1], 1, 1, 0)
				elif i == 2:
					gancio(_v, self.volumes[i + 1], 0, 0, 0)
		else:
			# cap linkage between buildings
			for i, _v in enumerate(self.volumes[:-1]):
				if i % 2 == 0:
					self.volumes[i + 1].mesh.rotation_euler[2] = radians(90)
				if i == 0:
					gancio(_v, self.volumes[i + 1], 1, 1, 0)
				elif i == 1:
					gancio(_v, self.volumes[i + 1], 1, 1, 0)
				elif i == 2:
					gancio(_v, self.volumes[i + 1], 1, 0, 1)

		return self.volumes

	def _correct_volumes(self):
		for v in self.volumes:
			v.width = min(max(v.width, self.width[0]), self.width[1])
			v.length = v.width * (np.random.random() + 1.5)
			v.height = max(min(v.height, min(v.width * 3, MAX_HEIGHT)), MIN_HEIGHT)
			v.create()
		self.volumes = sorted(self.volumes, key=lambda x: x.length)


class PatioEqual(Patio):
	"""
	Class that represents a Patio building with equal height volumes.
	"""

	def __init__(self, volumes):
		Patio.__init__(self, volumes)

	def _correct_volumes(self):
		_height = max(min(self.volumes[0].height, min(self.volumes[0].width * 3,
		                                              MAX_HEIGHT)), MIN_HEIGHT)
		for v in self.volumes:
			v.width = min(max(v.width, self.width[0]), self.width[1])
			v.length = v.width * (np.random.random() + 1.5)
			v.height = _height
			v.create()
		self.volumes = sorted(self.volumes, key=lambda x: x.length)


class ClosedPatio(Patio):
	"""
	Class that represents a Patio building with equal height volumes.
	"""

	def __init__(self, volumes):
		Patio.__init__(self, volumes)
		assert len(self.volumes) == 2, "Expected 2 volumes for Closed Patio, " \
		                               "got {}".format(len(self.volumes))

	def _correct_volumes(self):
		for v in self.volumes:
			v.width = min(max(v.width, self.width[0]), self.width[1])
			v.length = v.width * (np.random.random() + 1.5)
			v.height = max(min(v.height, min(v.width * 3, MAX_HEIGHT)),
		              MIN_HEIGHT)
			v.create()

		for v in self.volumes[:2]:
			v1 = Factory().produce(scale=(v.width, v.length, v.height))
			self.volumes.append(v1)


class TBuilding(ComposedBuilding):
	"""
	Class that represents a T-shaped building with random location of the
	second volume along the side of the first volume.
	"""
	def __init__(self, volumes):
		ComposedBuilding.__init__(self, volumes)
		assert len(volumes) == 2, "L-shaped bulding can be composed of 2 volumes" \
		                          "only, got {}".format(len(volumes))

	def make(self):
		self._correct_volumes()
		x_min, x_max = get_min_max(self.volumes[0].mesh, 0)  # width
		y_min, y_max = get_min_max(self.volumes[0].mesh, 1)  # length

		if random.random() < 0.5:
			self.volumes[1].mesh.location[0] = random.choice(np.linspace(int(x_min + (self.volumes[1].length)),
				      int(x_max - (self.volumes[1].length)), 10))
			self.volumes[1].mesh.location[1] = y_min - self.volumes[1].width

		else:
			self.volumes[1].mesh.location[1] = random.choice(np.linspace(
				int(y_min + (self.volumes[1].width)),
				int(y_max - (self.volumes[1].width)), 10))
			self.volumes[1].mesh.location[0] = x_min - self.volumes[1].length

		return self.volumes


class Skyscraper(ComposedBuilding):
	"""
	Class that represents a Skyscraper building with height significantly larger
	than width or length of the building.
	"""

	def __init__(self, volumes):
		ComposedBuilding.__init__(self, volumes)

	def _correct_volumes(self):
		for _v in self.volumes:
			_v.height = np.random.randint(100, 200)
			_v.length = max(30, _v.length)
			_v.width = max(30, _v.width)
			_v.create()


class EBuilding(ComposedBuilding):
	"""
	Class that represents a E-shaped building with random locations of the
	volumes along the side of the first volume.
	"""
	def __init__(self, volumes):
		ComposedBuilding.__init__(self, volumes)

	def make(self):

		self._correct_volumes()
		x_min, x_max = get_min_max(self.volumes[0].mesh, 0)  # width
		y_min, y_max = get_min_max(self.volumes[0].mesh, 1)  # length

		if random.random() < 0.5:
			for _volume in self.volumes[1:]:
				_volume.mesh.location[0] = random.choice(np.linspace(int(x_min + (_volume.length)),
					      int(x_max - (_volume.length)), 10))
				_volume.mesh.location[1] = y_min - _volume.width

		else:
			for _volume in self.volumes[1:]:
				_volume.mesh.location[1] = random.choice(np.linspace(
					int(y_min + (_volume.width)),
					int(y_max - (_volume.width)), 10))
				_volume.mesh.location[0] = x_min - _volume.length

		return self.volumes


if __name__ == '__main__':

	NUM_IMAGES = 1
	for image in range(NUM_IMAGES):
		f = CollectionFactory()
		collection = f.produce(number=np.random.randint(1, 4))
		building = ComposedBuilding(collection.collection)
		building.make()

		axis = 1

		for j, v in enumerate(collection.collection):

			mod = GridApplier(Window)
			w = Window()
			w.connect(v, 1)
			step = (np.random.randint(1, 6), np.random.randint(1, 6))
			if j == 0:
				mod.apply(w, step=step, offset=(2.0, 2.0, 2.0, 1.0))
			else:
				mod.apply(w, step=step)

			w = Window()
			w.connect(v, 0, 0)
			step = (np.random.randint(1, 6), np.random.randint(1, 6))
			if j == 0:
				mod.apply(w, step=step, offset=(2.0, 2.0, 2.0, 1.0))
			else:
				mod.apply(w, step=step)

		renderer = Renderer(mode=0)
		renderer.render(filename='building_{}'.format(image))
		building.save(image)
		building.save(image, ext='ply')
		building.demolish()
		cloud = PointCloud()
		cloud.make(image)
		# cloud = PyntCloud.from_file("Models/{}.obj".format(image))
		# cloud.to_file("{}.ply".format(image))
		# cloud.to_file("{}.npz".format(image))


