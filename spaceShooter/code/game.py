import pygame
import sys
from os.path import join
from random import randint, uniform

class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.image.load(join('..', 'images', 'player.png')).convert_alpha()
        self.rect = self.image.get_frect(center = (1280 / 2, 720 / 2))
        self.direction = pygame.Vector2()
        self.speed = 700
        
        self.shoot = True
        self.shootTime = 0
        self.cooldown = 300

    def laserTimer(self):
        
        if not self.shoot:
            currentTime = pygame.time.get_ticks()
            if currentTime - self.shootTime >= self.cooldown:
                self.shoot = True
            

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.direction.y = int(keys[pygame.K_DOWN] or keys[pygame.K_s]) - int(keys[pygame.K_UP] or keys[pygame.K_w])
        self.direction = self.direction.normalize() if self.direction else self.direction
        self.rect.center += self.direction * self.speed * dt

        recent_keys = pygame.key.get_just_pressed()
        if recent_keys[pygame.K_SPACE] and self.shoot:
            Laser(laserSurf, self.rect.midtop, (allSprites, laserSprites))
            self.shoot = False
            self.shootTime = pygame.time.get_ticks()
            laserSound.play()
        self.laserTimer()

class Star(pygame.sprite.Sprite):
    def __init__(self, groups, surf):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(center = (randint(0, 1280), randint(0, 720)))
        
class Laser(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(midbottom = pos)
    def update(self, dt):
        self.rect.centery -= 400 * dt
        if self.rect.bottom < 0:
            self.kill()

class Meteor(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.originalSurf = surf
        self.image = surf
        self.rect = self.image.get_frect(center = pos)
        self.start = pygame.time.get_ticks()
        self.lifetime = 3000
        self.direction = pygame.Vector2(uniform(-0.5, 0.5), 1)
        self.speed = randint(400, 600)
        self.rotationSpeed = randint(50, 90)
        self.rotation = 0

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        if pygame.time.get_ticks() - self.start >= self.lifetime:
            self.kill()
        self.rotation += self.rotationSpeed * dt
        self.image = pygame.transform.rotozoom(self.originalSurf, self.rotation, 1)
        self.rect = self.image.get_frect(center = self.rect.center)
class explosion(pygame.sprite.Sprite):
    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames
        self.frameIndex = 0
        self.image = frames[self.frameIndex]
        self.rect = self.image.get_frect(center = pos)
    def update(self, dt):
        self.frameIndex += 20 * dt
        if self.frameIndex < len(self.frames):
            self.image = self.frames[int(self.frameIndex)]
        else:
            self.kill()
def collisions():
    global running
    spriteCollision = pygame.sprite.spritecollide(player, meteorSprites, True, pygame.sprite.collide_mask)
    if spriteCollision:
        running = False
    for laser in laserSprites:
        collidedSprites = pygame.sprite.spritecollide(laser, meteorSprites, True)
        if collidedSprites:
            laser.kill()
            explosion(explosionFrames, laser.rect.midtop, allSprites)
            meteorExplosion.play()

def score():
    time = pygame.time.get_ticks() // 10
    textSurf = font.render(str(time), True, (255, 255, 255))
    textRect = textSurf.get_frect(midbottom = (1280 / 2, 720 - 50))
    screen.blit(textSurf, textRect)
    pygame.draw.rect(screen, (255, 255, 255), textRect.inflate(30, 20).move(0,-2), 3, 6)
pygame.mixer.init()
pygame.init()

running = True
screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption('space shooter')
clock = pygame.time.Clock()

starSurf = pygame.image.load(join('..', 'images', 'star.png')).convert_alpha()
laserSurf = pygame.image.load(join('..', 'images', 'laser.png')).convert_alpha()
meteorSurf = pygame.image.load(join('..', 'images', 'meteor.png')).convert_alpha()
font = pygame.font.Font(join('..','images', 'Oxanium-Bold.ttf'), 20)
explosionFrames = [pygame.image.load(join('..','images','explosion', f'{i}.png')).convert_alpha() for i in range(21)]
laserSound = pygame.mixer.Sound(join('..', 'audio', 'laser.wav'))
meteorExplosion = pygame.mixer.Sound(join('..', 'audio', 'explosion.wav'))
meteorExplosion.set_volume(0.7)
gameMusic = pygame.mixer.Sound(join('..', 'audio', 'game_music.wav'))
gameMusic.set_volume(0.5)
gameMusic.play(loops = -1)
allSprites = pygame.sprite.Group()
meteorSprites = pygame.sprite.Group()
laserSprites = pygame.sprite.Group()

for i in range(20):
    Star(allSprites, starSurf)
player = Player(allSprites)

meteorEvent = pygame.event.custom_type()
pygame.time.set_timer(meteorEvent, 300)


while(running):

    dt = clock.tick() / 1000
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == meteorEvent:
            x, y = randint(0, 1280), randint(-200, -100)
            Meteor(meteorSurf, (x, y), (allSprites, meteorSprites))
    collisions()
    
    allSprites.update(dt)

    screen.fill('black')
    score()
    allSprites.draw(screen)
    
    pygame.display.update()

pygame.quit()

