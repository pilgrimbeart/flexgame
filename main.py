import pygame
import time
import random
from datetime import date
from PIL import Image, ImageEnhance
from math import sin
import sys, os

NUM_TEAMS = 3

team_colours = [
        (255,0,0),
        (0,255,0),
        (0,0,255)
        ]

pygame.init()
pygame.mixer.init()
pygame.mouse.set_visible(False)

sound_file_names = [
        ("laser-zap-2-90669.mp3", "zap"),
        ("ready-fight-37973.mp3", "ready"),
        ("drum-and-bass-drums-loop-160-bpm-1-131244.mp3", "dnb_loop"),
        ("huge-hit-logo-143925.mp3", "hit"),
        ("success-1-6297.mp3", "success"),
        ("buzzer-15-187758.mp3", "buzzer"),
        ("you-win-sequence-3-183950.mp3","win"),
        ("not-charged.mp3","notcharged")
]
sounds = {}
for filename,short in sound_file_names:
    sounds[short] = pygame.mixer.Sound(filename)

prices = [[] for _ in range(365)]
def read_energy_prices():
    global prices
    for line in open("epex_hourly_auction_outturn_2023onwards.csv","rt").readlines()[1:]:
        datetime, price, volume = line.split(",")
        day,month,year = datetime.split(" ")[0].split("/")
        if year=="2023":
            day_of_year = date(int(year),int(month),int(day)).timetuple().tm_yday-1
            hour = datetime.split(" ")[1].split(":")[0]
            prices[day_of_year].append(float(price))     # RELIES ON DATA BEING SORTED!

def draw_price_chart(day):
    pygame.draw.line(screen, (128,128,128), (pricechart_left, 0), (pricechart_left, pricechart_bottom), 2)
    pygame.draw.line(screen, (128,128,128), (pricechart_left, pricechart_bottom), (screen_width, pricechart_bottom), 2)
    pygame.draw.line(screen, (128,128,128), (screen_width, pricechart_bottom), (screen_width, 0), 2)
    pygame.draw.line(screen, (128,128,128), (screen_width, 0), (pricechart_left, 0), 2)
    wid = screen_width - pricechart_left
    hgt = pricechart_bottom
    xscale = wid/24
    yscale = 1
    lines = []
    for hour in range(24):
        lines.append( (pricechart_left + hour * xscale, pricechart_bottom - prices[day][hour]) )
    pygame.draw.lines(screen, (255,128,128), False, lines, 5) 

def draw_charging_hour(team, hour, fill):
    lines = []
    left = screen_width / 2
    top = screen_height / 2
    xscale = (screen_width / 2 ) / 24
    yscale = (screen_height / 2) / NUM_TEAMS
    lines.append( (left + hour * xscale, top + team * yscale) )
    lines.append( (left + (hour+1) * xscale, top + team * yscale) )
    lines.append( (left + (hour+1) * xscale, top + (team+1) * yscale) )
    lines.append( (left + hour * xscale, top + (team+1) * yscale) )
    pygame.draw.polygon(screen, fill, lines)
    pygame.draw.lines(screen, (192, 192, 192), True, lines, 1)

car_images = []
def load_car_image(imagename):
    global car_images
    image = pygame.image.load(imagename).convert_alpha()  # Maintain transparency
    scale_factor = car_height / image.get_height() 
    scaled_image = pygame.transform.scale(image, ( int(image.get_width() * scale_factor), int(image.get_height() * scale_factor)))
    car_images.append(scaled_image)

def start_countdown():
    global mode, start_time, charge_level, charging_hours
    mode = "COUNTDOWN"
    start_time = time.time()
    sounds["ready"].play()
    charge_level = [0.2 for i in range(NUM_TEAMS)]
    charging_hours = [[False for __ in range(24)] for _ in range(NUM_TEAMS)]

def restart_game(): 
    global round, current_day, cash, mode, start_time, charge_level, charging_hours
    round = 0
    current_day = 0
    cash = [9.99 for i in range(NUM_TEAMS)]

    # start_countdown()
    mode = "IDLE"
    start_time = time.time()
    charge_level = [0.2 for i in range(NUM_TEAMS)]
    charging_hours = [[False for __ in range(24)] for _ in range(NUM_TEAMS)]

    sounds["dnb_loop"].stop()

read_energy_prices()

display_info = pygame.display.Info()
screen_width, screen_height = display_info.current_w, display_info.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.NOFRAME)
pygame.key.set_repeat(500, 50)  # 500ms delay, 50ms interval
# Set object dimensions based on screen size
pricechart_left = screen_width/2
pricechart_bottom = screen_height/2
car_height = screen_width/6


for image in ["abarth_red.png", "abarth_green.png", "abarth_blue.png"]:
    load_car_image(image)

font = pygame.font.Font("Quicksand-Regular.ttf", 50)

large_font = pygame.font.Font("Quicksand-Bold.ttf", 512)
countdown_numbers = []
for i in range(4):
    countdown_numbers.append(large_font.render(str(i), True, (0,0,0)))

running = True

restart_game()

while running:
    screen.fill((255,255,255))
    current_hour = int(time.time()-start_time)

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == 27:
                running = False
            if event.key == pygame.K_UP:
                current_day = (current_day+1) % 365
            if event.key == pygame.K_DOWN:
                current_day = (current_day-1+365) % 365
            if event.key == ord("r"):
                restart_game()
            if event.key == ord(" "):
                if mode in ["IDLE","SCORING"]:
                    round += 1
                    start_countdown()

        if event.type == pygame.TEXTINPUT:  # For footswitch devices, this deals with repeats better than keydown
            if (event.text[0] >= "1") and (event.text[0] <= chr(ord("0")+NUM_TEAMS)):
                team = ord(event.text[0]) - ord("1")
                if (team < NUM_TEAMS) and (mode=="PLAY"):
                    if not charging_hours[team][current_hour]:
                        if charge_level[team] < 1.0:
                            charging_hours[team][current_hour] = True
                            sounds["zap"].stop()
                            sounds["zap"].play()
                            charge_level[team] += 0.1
                            if charge_level[team] >= 0.98:  # Close-enough
                                charge_level[team] = 1.0
                                sounds["success"].play()
                            cash[team] -= 7 * (prices[current_day][current_hour] / 1000) # 7kWh per h, and convert £/MWH to £/kWh
        if event.type == pygame.QUIT:
            running = False

    # RENDER
    text_surface = font.render("Round "+str(round), True, (0,0,0))
    screen.blit(text_surface, (0,0))
    text_surface = font.render("Day "+str(current_day), True, (0,0,0))  # TODO: Only on change
    screen.blit(text_surface, (0,50))

    for team in range(NUM_TEAMS):
        spacing = (screen_height/2) / NUM_TEAMS
        top = screen_height/2 + float(team) * spacing
        bottom = screen_height/2 + float(team+1) * spacing

        # Car
        if (mode=="FINISHED") and (charge_level[team] < 1.0) and random.random() > 0.5: # Make car flicker if it fails to charge
            pass
        else:
            screen.blit(car_images[team], (0, top)) 
            text_surface = font.render(str(team+1), True, (255,255,255))
            screen.blit(text_surface, (90, top+80))

            # Charge level
            x = screen_width/2 - 50
            rect_height = spacing-10
            pygame.draw.rect(screen, team_colours[team], pygame.Rect(x,top,20,rect_height), width=1, border_radius=10) 
            pygame.draw.rect(screen, team_colours[team], pygame.Rect(x,top*charge_level[team]+bottom*(1-charge_level[team]),20, rect_height * charge_level[team]), width=0, border_radius=10)

        if mode=="SCORING":
            if cash[team] >= max(cash):
                image = pygame.image.load("first.png").convert_alpha() 
                scale_factor = (0.7 + 0.5 * sin(time.time()*4)) * (car_height / image.get_height()) / 2 # Make the "1st" symbol about half the size of the car
                scaled_image = pygame.transform.scale(image, ( int(image.get_width() * scale_factor), int(image.get_height() * scale_factor)))
                screen.blit(scaled_image, (100,top))

        # Cash
        text_surface = font.render(f"£{cash[team]:.2f}", True, (0,0,0))
        screen.blit(text_surface, (x-200, top))

        for hour in range(24):
            colour = (255,255,255)
            if (mode=="PLAY") and (hour==current_hour):
                if random.random()>0.5:
                    colour = (255,255,0)
            if charging_hours[team][hour]:
                colour = team_colours[team]
            draw_charging_hour(team, hour, colour)

    draw_price_chart(current_day)

    if mode=="COUNTDOWN":
        t = time.time() - start_time
        if t < 3:
            i = int(t)
            ts = t % 1
            scale = (screen_height) / (1 + ts)
            c = pygame.transform.scale(countdown_numbers[3-i], (scale,scale))
            c.set_alpha(128)
            screen.blit(c, (screen_width/2 - scale/2, screen_height/2 - scale/2))
        else:
            mode = "PLAY"
            start_time = time.time()
            sounds["dnb_loop"].set_volume(0.3)
            sounds["dnb_loop"].play(-1)

    if mode=="PLAY":
        if current_hour>23:
            sounds["dnb_loop"].stop()
            sounds["hit"].play()
            mode = "FINISHED"
            start_time=time.time()
            for team in range(NUM_TEAMS): # Check for inadequate charging
                if charge_level[team] < 1:
                    sounds["buzzer"].play()

    if mode=="FINISHED":
        for team in range(NUM_TEAMS):
            if charge_level[team] < 1.0:
                cash[team] = max(0, cash[team] - 0.01)  # Drain it to zero!

        if time.time() > start_time + 5:
            mode = "SCORING"
            start_time = time.time()
            sounds["win"].play()

    pygame.display.flip()

# Quit Pygame
pygame.quit()
