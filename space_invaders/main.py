import numpy as np
import pygame as pg
from random import random, choice

INVADER_PIXELS = [[112, 24, 125, 182, 188, 60, 188, 182, 125, 24, 112],
                  [30, 184, 125, 54, 60, 60, 60, 54, 125, 184, 30]]
PLAYER_PIXELS = [224, 240, 240, 240, 240, 255, 240, 240, 240, 240, 224]
YOU_PIXELS = [143, 136, 136, 255, 0, 255, 129, 129, 255, 0, 255, 128, 128, 255]
WIN_PIXELS = [7, 56, 192, 32, 16, 32, 192, 56, 7, 0, 129, 129, 255, 129, 129, 0, 255, 2, 12, 48, 64, 255]
LOSS_PIXELS = [255, 128, 128, 128, 0, 255, 129, 129, 255, 0, 70, 137, 145, 98, 0, 255, 137, 137, 137]
BLOCK_PIXELS = [248, 254, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 254, 248]
FRAMES_FOR_SPRITE = 130
FRAMES_TO_MOVE_INVADERS = 180
FRAMES_TO_MOVE_PLAYER = 10
FRAMES_TO_MOVE_SHOTS = 10
FRAMES_TO_FIRE_PLAYER = 160
FRAMES_TO_FIRE_INVADER = 100
CHANCE_TO_FIRE = .01
INVADER_ROWS = 4
INVADER_GAP = 4
BLOCK_AMOUNT = 6
PIXEL_SIZE = 4
WIDTH, HEIGHT = 200, 150

INVADER_WIDTH = len(INVADER_PIXELS[0])
PLAYER_WIDTH = len(PLAYER_PIXELS)
BLOCK_WIDTH = len(BLOCK_PIXELS)
INVADER_HEIGHT = PLAYER_HEIGHT = BLOCK_HEIGHT = 8
BLOCK_GAP = WIDTH//(BLOCK_AMOUNT+1)
SCREEN = np.zeros((WIDTH, HEIGHT))
xs = range(INVADER_WIDTH//2, WIDTH-2*INVADER_WIDTH, INVADER_WIDTH+INVADER_GAP)
ys = range(2*INVADER_HEIGHT, 2*INVADER_HEIGHT+(INVADER_HEIGHT+INVADER_GAP)*INVADER_ROWS, INVADER_HEIGHT+INVADER_GAP)
INVADERS = np.array([[x, y] for x in xs for y in ys])
PLAYER = [WIDTH//2 - PLAYER_WIDTH//2, HEIGHT-20]
BLOCKS = [[BLOCK_PIXELS.copy(), [x, PLAYER[1]-2*BLOCK_HEIGHT]] for x in
          range(BLOCK_GAP-BLOCK_WIDTH//2, BLOCK_AMOUNT*BLOCK_GAP+BLOCK_WIDTH//2, BLOCK_GAP)]
INVADER_SHOTS = []
PLAYER_SHOTS = []

BG_COLOR = (0, 0, 0)
FW_COLOR = (255, 255, 255)
going_left = False
going_right = False
player_firing = False

pg.init()
PG_SCREEN = pg.display.set_mode((WIDTH*PIXEL_SIZE, HEIGHT*PIXEL_SIZE))

def render(sprite: list[int], at: tuple[int, int]):
    for dx, column in enumerate(sprite):
        dy = 0
        while column:
            if column&1:
                SCREEN[at[0]+dx, at[1]+dy] = 1
            column>>=1
            dy+=1

def render_shots():
    for shot in PLAYER_SHOTS+INVADER_SHOTS:
        SCREEN[shot[0], shot[1]-1:shot[1]+2] = 1

def draw_screen(pg_screen):
    for x, column in enumerate(SCREEN):
        for y, pixel in enumerate(column):
            if pixel:
                pg.draw.rect(pg_screen, FW_COLOR, (x*PIXEL_SIZE, y*PIXEL_SIZE, PIXEL_SIZE, PIXEL_SIZE))

def render_all(animation_frame: int):
    PG_SCREEN.fill(BG_COLOR)
    SCREEN.fill(0)
    for invader in INVADERS:
        render(INVADER_PIXELS[animation_frame//FRAMES_FOR_SPRITE], invader)
    render(PLAYER_PIXELS, PLAYER)
    render_shots()
    for block in BLOCKS:
        render(*block)
    draw_screen(PG_SCREEN)
    pg.display.update()


def move_player():
    if going_left ^ going_right:
        PLAYER[0] += going_right - going_left

def move_invaders(movement_frame: int):
    for invader in INVADERS:
        if movement_frame % ((INVADER_WIDTH+1)*FRAMES_TO_MOVE_INVADERS) == 0:
            invader[1] += 3
        else:
            invader[0] += 1-2*(movement_frame // ((INVADER_WIDTH+1)*FRAMES_TO_MOVE_INVADERS))

def move_shots():
    remove = []
    for i, shot in enumerate(PLAYER_SHOTS):
        shot[1] -= 1
        if shot[1] == 0:remove.append(i)
    for i in reversed(remove):
        PLAYER_SHOTS.pop(i)
    remove = []
    for i, shot in enumerate(INVADER_SHOTS):
        shot[1] += 1
        if shot[1] == 0:remove.append(i)
    for i in reversed(remove):
        INVADER_SHOTS.pop(i)

def move(player_movement_frame: int, invader_movement_frame: int, shots_movement_frame: int):
    if shots_movement_frame % FRAMES_TO_MOVE_SHOTS == 0:
        move_shots()
    if player_movement_frame % FRAMES_TO_MOVE_PLAYER == 0:
        move_player()
    if invader_movement_frame % FRAMES_TO_MOVE_INVADERS == 0:
        move_invaders(invader_movement_frame)

def fire(player_fire_frame: int):
    if player_firing and player_fire_frame == 0:
        PLAYER_SHOTS.append([PLAYER[0]+PLAYER_WIDTH//2, PLAYER[1]])
    if random() < CHANCE_TO_FIRE:
        INVADER_SHOTS.append([choice(INVADERS)[0]+INVADER_WIDTH//2, choice(INVADERS)[1]+INVADER_HEIGHT])

def collide_invaders():
    global INVADERS
    remove_s = []
    for i, shot in enumerate(PLAYER_SHOTS):
        remove_i = []
        for j, invader in enumerate(INVADERS):
            if shot[0]>=invader[0] and abs(shot[0]-invader[0])<INVADER_WIDTH and \
                shot[1]>=invader[1] and abs(shot[1]-invader[1])<INVADER_HEIGHT:
                remove_s.append(i)
                remove_i.append(j)
        INVADERS = np.delete(INVADERS, remove_i, axis=0)
    for i in reversed(remove_s):
        PLAYER_SHOTS.pop(i)

def delete_pixel(sprite: list[int], at: tuple[int, int]):
    if 0 <= at[0] < len(sprite) and \
       0 <= at[1] < BLOCK_HEIGHT:
        full_column = (1<<BLOCK_HEIGHT)-1
        sprite[at[0]] &= (full_column - (1<<at[1]))

def break_block(sprite: list[int], at: tuple[int, int]):
    x, y = at
    for row in [[(dx, dy) for dx in range(abs(dy)-2, 3-abs(dy))] for dy in range(-2, 3)]:
        for dx, dy in row:
            delete_pixel(sprite, (x+dx, y+dy))

def collide_shots(shots: list[tuple[int, int]], block: tuple[tuple[int, int], list[int]], at: tuple[int, int]):
    remove = []
    for i, shot in enumerate(shots):
        if shot == [block[1][0]+at[0], block[1][1]+at[1]]:
            break_block(block[0], at)
            remove.append(i)
    for i in reversed(remove):
        shots.pop(i)

def collide_blocks():
    for block in BLOCKS:
        for dx, column in enumerate(block[0]):
            dy = 0
            while column:
                if column&1:
                    collide_shots(PLAYER_SHOTS, block, (dx, dy))
                    collide_shots(INVADER_SHOTS, block, (dx, dy))
                column>>=1
                dy+=1

def collide_player():
    for shot in INVADER_SHOTS:
        if shot[0]>=PLAYER[0] and abs(shot[0]-PLAYER[0])<INVADER_WIDTH and \
            shot[1]>=PLAYER[1] and abs(shot[1]-PLAYER[1])<INVADER_HEIGHT:
            return True
    return False

def collide():
    collide_invaders()
    collide_blocks()
    dead = collide_player()
    if len(INVADERS) == 0:
        return True
    if dead: return False
    return None


invader_animation_frame = 0
player_movement_frame = 0
invader_movement_frame = 0
shots_movement_frame = 0
player_fire_frame = 0
invader_fire_frame = 1
state = None
while True:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            quit()
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_SPACE:
                player_firing = True
            if event.key == pg.K_RIGHT:
                going_right = True
            if event.key == pg.K_LEFT:
                going_left = True
        if event.type == pg.KEYUP:
            if event.key == pg.K_SPACE:
                player_firing = False
            if event.key == pg.K_RIGHT:
                going_right = False
            if event.key == pg.K_LEFT:
                going_left = False
    
    fire(player_fire_frame)
    move(player_movement_frame, invader_movement_frame, shots_movement_frame)
    state = collide()
    if state is not None:
        break
    render_all(invader_animation_frame)
    player_movement_frame = (player_movement_frame + 1) % FRAMES_TO_MOVE_PLAYER
    invader_movement_frame = (invader_movement_frame + 1) % (2*(INVADER_WIDTH+1)*FRAMES_TO_MOVE_INVADERS)
    shots_movement_frame = (shots_movement_frame + 1) % FRAMES_TO_MOVE_SHOTS
    invader_animation_frame = (invader_animation_frame + 1) % (len(INVADER_PIXELS)*FRAMES_FOR_SPRITE)
    invader_fire_frame = (invader_fire_frame + 1) % FRAMES_TO_FIRE_INVADER
    if player_firing and player_fire_frame == 0: player_fire_frame = FRAMES_TO_FIRE_PLAYER
    if player_fire_frame: player_fire_frame -= 1

PIXEL_SIZE *= 2

if state is True:
    pixels = WIN_PIXELS
if state is False:
    pixels = LOSS_PIXELS
final_screen = pg.display.set_mode((PIXEL_SIZE*(len(YOU_PIXELS)+4+len(pixels)+4), PIXEL_SIZE*12))
render(YOU_PIXELS+4*[0]+pixels, at = (2, 2))
draw_screen(final_screen)
while True:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            quit()
    pg.display.update()