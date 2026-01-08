import pygame 
import sys
from level import Level
from pytmx.util_pygame import load_pygame
from settings import *
from os.path import join

class Game:
	def __init__(self):
		self.display_surface = pygame.display.set_mode((1280, 720))
		pygame.display.set_caption('tiny toon world')
		self.clock = pygame.time.Clock()

		self.tmx_maps = {0: load_pygame(join('..', 'data', 'levels', 'omni.tmx'))}

		self.current_stage = Level(self.tmx_maps[0])

	def run(self):
		while True:
			dt = self.clock.tick() / 1000
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
			self.current_stage.run(dt)
			pygame.display.update()

Game().run()