import os
import sys

sys.path.append("D:\ProgramFiles\Anaconda\envs\py37\Lib\site-packages")
from pyntcloud import PyntCloud

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)

from dataset_config import *


# Question: how many points per building (2048) - ModelNet40

class PointCloud:
	def __init__(self):
		self.points = POINTS

	def make(self, filename):
		self._make(filename)

	def _make(self, filename):
		print(filename)
		cloud = PyntCloud.from_file("{}/{}.ply".format(CLOUD_SAVE, filename))
		cloud = cloud.get_sample('mesh_random', n=self.points, rgb=False,
		                         normals=True, as_PyntCloud=True)
		cloud.to_file("{}/{}.ply".format(CLOUD_SAVE, filename))





