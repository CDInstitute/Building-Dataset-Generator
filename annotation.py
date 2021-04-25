import bpy
import json
import numpy as np
import os
import sys

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)

from dataset_config import *


class Annotation:
	"""
	Class that writes an annotation based on Pix3D dataset structure from an
	active 3D scene.

	"""
	def __init__(self):
		self.content = {}
		self.full = []
		self._clean()

	def add(self, building, name, model):
		"""
		Function that adds a model's annotation to the full dataset annotation.
		:param building: building to add to json, Building class
		:param name: name of the image file, str
		:param model: name of the model .obj file, str
		:return:
		"""
		assert isinstance(name, str)

		self.content['img'] += name
		self.content['mask'] += name.split('/')[-1]
		self.content['point_cloud'] += name.split('/')[-1]
		self.content['model'] += model

		try:
			self.content['cam_position'] = list(bpy.data.objects['Camera'].location)
			self.content['cam_position'] = [round(x, 3) for x in
			                                self.content['cam_position']]
		except Exception:
			pass
		try:
			self.content['focal_length'] = round(bpy.data.cameras['Camera'].lens, 3)

		except Exception:
			pass

		for v in building.volumes:
			try:
				self.content['material'].append(v.mesh.active_material.name.split('.')[0])
			except Exception:
				pass
		self.content['material'] = list(set(self.content['material']))
		self.content['img_size'] = (bpy.data.scenes[0].render.resolution_y,
		                            bpy.data.scenes[0].render.resolution_x)
		self.content['bbox'] = building.get_bb()
		self.full.append(self.content)
		self._clean()

	def write(self, filename='test.json'):
		"""
		Function that writes the full json annotation to the provided location.
		:param filename: name of the file to write, str, default='test.json'
		:return:
		"""
		assert isinstance(filename, str), 'Expected filename to be str, got {}'.format(type(filename))
		with open(filename, 'w') as f:
			json.dump(self.full, f)

		print('Annotation successfully written as {}'.format(filename))

	def _clean(self):
		"""
		Function that returns the annotation template to its default form.
		:return:
		"""
		self.content = {'img': IMG_SAVE + '/',
		                'category': 'building',
		                'img_size': IMAGE_SIZE,
		                '2d_keypoints': [],
		                'mask': 'masks/',
		                'img_source': 'synthetic',
		                'model': MODEL_SAVE + '/',
		                'point_cloud': CLOUD_SAVE + '/',
		                'model_raw': 0,
		                'model_source': 'synthetic',
		                'trans_mat': 0,
		                'focal_length': 35.0,
		                'cam_position': (0.0, 0.0, 0.0),
		                'inplane_rotation': 0,
		                'truncated': False,
		                'occluded': False,
		                'slightly_occluded': False,
		                'bbox': [0.0, 0.0, 0.0, 0.0],
		                'material': []}

