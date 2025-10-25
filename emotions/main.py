import pygame
import yaml
import sys
import random

""" cargar configuración desde config.yaml """
with open('emotions/config.yaml', 'r') as file:
    config = yaml.safe_load(file)

COLOR_FONDO = tuple(config['COLOR_FONDO'])
COLOR_PIXEL = tuple(config['COLOR_PIXEL'])
ANCHO_PANTALLA = config['ANCHO_PANTALLA']
ALTO_PANTALLA = config['ALTO_PANTALLA']
ANCHO_PIXEL = config['ANCHO_PIXEL']
ALTO_PIXEL = config['ALTO_PIXEL']

""" definiciones de las matrices de emociones (frames) """
CARA_NORMAL = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
    [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
    [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]

CARA_NORMAL_PARPADEO = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]

CARA_FELIZ = [
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
    [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
]

CARA_FELIZ_PARPADEO = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]

CARA_TRISTE = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1],
    [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]

CARA_TRISTE_PARPADEO = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]

ANIMACIONES = [
    [CARA_NORMAL, CARA_NORMAL_PARPADEO],  # normal con parpadeo
    [CARA_FELIZ, CARA_FELIZ_PARPADEO],     # feliz con parpadeo
    [CARA_TRISTE, CARA_TRISTE_PARPADEO]   # triste con parpadeo
]

emocion_actual = 0
frame_actual = 0

parpadeando = False
proximo_parpadeo = 0
fin_parpadeo = 0

def reiniciar_parpadeo():
    global parpadeando, proximo_parpadeo, fin_parpadeo, frame_actual
    parpadeando = False
    frame_actual = 0
    ahora = pygame.time.get_ticks()
    proximo_parpadeo = ahora + random.randint(140, 220)
    fin_parpadeo = 0

""" dibuja una emoción en la superficie dada """
def dibujarEmocion(superficie, emocion):
    superficie.fill(COLOR_FONDO)

    ancho_emocion = len(emocion[0]) * ANCHO_PIXEL
    alto_emocion = len(emocion) * ALTO_PIXEL

    offset_x = (ANCHO_PANTALLA - ancho_emocion) // 2
    offset_y = (ALTO_PANTALLA - alto_emocion) // 2

    for y, fila in enumerate(emocion):
        for x, pixel in enumerate(fila):
            if pixel == 1:
                rect = (offset_x + x * ANCHO_PIXEL,
                        offset_y + y * ALTO_PIXEL,
                        ANCHO_PIXEL,
                        ALTO_PIXEL)
                pygame.draw.rect(superficie, COLOR_PIXEL, rect)

""" inicialización de Pygame """
pygame.init()
screen = pygame.display.set_mode((ANCHO_PANTALLA, ALTO_PANTALLA))
pygame.display.set_caption("KUBIBOT Emociones")
screen.fill(COLOR_FONDO)
clock = pygame.time.Clock()
reiniciar_parpadeo()

""" Bucle principal """
running = True
while running:
    dt = clock.tick(60)
    ahora = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            # Mapea teclas a emociones específicas
            if event.key == pygame.K_a:
                emocion_actual = 0  # normal
                reiniciar_parpadeo()
            if event.key == pygame.K_s:
                emocion_actual = 1  # feliz
                reiniciar_parpadeo()
            if event.key == pygame.K_d:
                emocion_actual = 2  # triste
                reiniciar_parpadeo()

    frames = ANIMACIONES[emocion_actual]
    if len(frames) > 1:
        if not parpadeando and ahora >= proximo_parpadeo:
            parpadeando = True
            frame_actual = 1
            fin_parpadeo = ahora + random.randint(140, 220)
        elif parpadeando and ahora >= fin_parpadeo:
            parpadeando = False
            frame_actual = 0
            proximo_parpadeo = ahora + random.randint(700, 1600)
    else:
        frame_actual = 0

    dibujarEmocion(screen, frames[frame_actual])
    pygame.display.flip()

pygame.quit()
sys.exit()