from settings import *
from sprites import Sprite
from player import Player
import pygame, sys

class Level:
	def __init__(self, tmx_map):
		self.display_surface = pygame.display.get_surface()
		self.all_sprites = pygame.sprite.Group()
		self.collision_sprites = pygame.sprite.Group()
		self.setup(tmx_map)

	def setup(self, tmx_map):
		for x, y, surf in tmx_map.get_layer_by_name('Terrain').tiles():
			Sprite((x * 64, y * 64), surf, (self.all_sprites, self.collision_sprites))
		
		for obj in tmx_map.get_layer_by_name('Objects'):
			if obj.name == 'player':
				Player((obj.x, obj.y), self.all_sprites, self.collision_sprites)
                
	def run(self, dt):
		self.display_surface.fill('black')
		self.all_sprites.update(dt)
		self.all_sprites.draw(self.display_surface)