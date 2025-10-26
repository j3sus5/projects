from settings import * 
import pygame, sys

class Sprite(pygame.sprite.Sprite):
	def __init__(self, pos, surf, groups):
		super().__init__(groups)
		self.image = pygame.Surface((64, 64))
		self.image.fill('white')
		self.rect = self.image.get_frect(topleft = pos)
		self.old_rect = self.rect.copy()