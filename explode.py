# explode.py - do explosion effects
import pygame
import random

class Explosion:
    def __init__(self, position, colour):
        self.position = position
        self.colour = colour
        self.size = 8
        self.delta = (random.random()*2-1.0, random.random()*2-1.0)
        self.life = 100

    def render(self, screen):
        pygame.draw.rect(screen, self.colour, (self.position[0]-self.size/2, self.position[1]-self.size/2, self.size, self.size))
        self.position = (self.position[0] + self.delta[0], self.position[1] + self.delta[1])
        self.life -= 1
        if self.life <= 0:
            explosions.remove(self)

explosions = []

def explode(x,y, colour): # Start explosion at (x,y)
    for particle in range(30):
        explosions.append(Explosion((x,y), colour))

def render(screen):
    for e in explosions:
        e.render(screen)

