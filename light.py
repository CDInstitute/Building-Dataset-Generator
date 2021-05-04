import bpy
import numpy as np


class LightManager:
	def __init__(self):
		self.name = 'Sun'
		self.object = bpy.data.objects[self.name]
		self.light = bpy.data.lights[self.name]
		self.light.type = 'SUN'

	def make(self):
		self._make()

	def _make(self):
		self.light.angle = np.radians(np.random.randint(0, 75) + np.random.random())
		self.object.rotation_euler[0] = np.radians(np.random.randint(0, 90) + np.random.random())
		self.object.rotation_euler[1] = np.radians(np.random.randint(0, 90) + np.random.random())
		self.object.rotation_euler[2] = np.radians(np.random.randint(0, 360) + np.random.random())
		self.light.energy = np.random.randint(3, 50) + np.random.random()
		for i in range(3):
			self.light.color[i] = 1.0
			if np.random.random() < 0.5:
				self.light.color[i] = np.random.uniform(0.78, 1.0)