import pygame
import time
import random
from datetime import date
from PIL import Image, ImageEnhance
from math import sin
import sys, os
import explode

NUM_TEAMS = 5
NUM_ROUNDS = 3

prices = [ # Pence per kWh. 24h per round.
        [10,10,10,11,11,10,12,12,13,14,13,15,17,20,20,21,23,24,26,26,25,26,25,26],
        [20,19,20,21,19,19,18,14,10,11,10,11,10, 9, 8,12,13,14,17,18,19,20,21,21],
        [20,19,20,21,23,23,24,25,26,26,26,25,24,23,20,18,16,14, 9, 4, 3, 4, 0, 0]
        ]

player_graphics = ["wall-e.png", "eve.png", "mo.png", "sentry.png", "go-4.png"]

team_colours = [
        (255,0,0),
        (0,255,0),
        (0,0,255),
        (255,165,0),
        (255,192,203)
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
        ("not-charged.mp3","notcharged"),
        ("realitycoming-69491.mp3","anticipation")
]
sounds = {}
for filename,short in sound_file_names:
    sounds[short] = pygame.mixer.Sound(filename)

#prices = [[] for _ in range(365)]
#def read_energy_prices():
#    global prices
#    for line in open("epex_hourly_auction_outturn_2023onwards.csv","rt").readlines()[1:]:
#        datetime, price, volume = line.split(",")
#        day,month,year = datetime.split(" ")[0].split("/")
#        if year=="2023":
#            day_of_year = date(int(year),int(month),int(day)).timetuple().tm_yday-1
#            hour = datetime.split(" ")[1].split(":")[0]
#            prices[day_of_year].append(float(price))     # RELIES ON DATA BEING SORTED!
#read_energy_prices()

def draw_price_chart(day):
    pygame.draw.line(screen, (128,128,128), (pricechart_left, 0), (pricechart_left, pricechart_bottom), 2)
    pygame.draw.line(screen, (128,128,128), (pricechart_left, pricechart_bottom), (screen_width, pricechart_bottom), 2)
    pygame.draw.line(screen, (128,128,128), (screen_width, pricechart_bottom), (screen_width, 0), 2)
    pygame.draw.line(screen, (128,128,128), (screen_width, 0), (pricechart_left, 0), 2)
    wid = screen_width - pricechart_left
    hgt = pricechart_bottom
    xscale = wid/24
    yscale = pricechart_bottom / 27 # 27p is max price
    lines = []
    for hour in range(24):
        lines.append( (pricechart_left + hour * xscale, pricechart_bottom - prices[day][hour] * yscale) )
    pygame.draw.lines(screen, (255,128,128), False, lines, 5) 

def draw_charging_hour(team, hour, fill):
    lines = []
    left = pricechart_left
    top = pricechart_bottom
    xscale = (screen_width - pricechart_left) / 24
    yscale = (screen_height - pricechart_bottom) / NUM_TEAMS
    l = left + hour * xscale
    t = top + team * yscale
    if fill != None:
        pygame.draw.rect(screen, fill, pygame.Rect(l,t,xscale,yscale), width=0, border_radius=10)  # Fill
    pygame.draw.rect(screen, (128,128,128), pygame.Rect(l,t,xscale,yscale), width=1, border_radius=10)  # Border


    #lines.append( (left + hour * xscale, top + team * yscale) )
    #lines.append( (left + (hour+1) * xscale, top + team * yscale) )
    #lines.append( (left + (hour+1) * xscale, top + (team+1) * yscale) )
    #lines.append( (left + hour * xscale, top + (team+1) * yscale) )
    #if fill:
    #    pygame.draw.polygon(screen, fill, lines)
    #pygame.draw.lines(screen, (0,0,0), True, lines, 2)

def load_image(imagename, target_width, target_height):
    image = pygame.image.load(imagename).convert_alpha()  # Maintain transparency
    if not target_width:
        scale_factor = target_height / image.get_height() 
        scaled_image = pygame.transform.scale(image, ( int(image.get_width() * scale_factor), int(image.get_height() * scale_factor)))
    else:
        scaled_image = pygame.transform.scale(image, (target_width, target_height))
    return scaled_image

def start_countdown():
    global mode, start_time, charge_level, charging_hours
    mode = "COUNTDOWN"
    start_time = time.time()
    sounds["ready"].play()

def reset_charge():
    global charge_level, charging_hours
    charge_level = [0.2 for i in range(NUM_TEAMS)]
    charging_hours = [[False for __ in range(24)] for _ in range(NUM_TEAMS)]

def restart_game(): 
    global round, cash, mode, start_time, charge_level, charging_hours
    round = 0
    cash = [0.00 for i in range(NUM_TEAMS)]

    # start_countdown()
    mode = "IDLE"
    start_time = time.time()
    reset_charge()

    sounds["dnb_loop"].stop()

display_info = pygame.display.Info()
screen_width, screen_height = display_info.current_w, display_info.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.NOFRAME)
pygame.key.set_repeat(500, 50)  # 500ms delay, 50ms interval
# Set object dimensions based on screen size
pricechart_left = screen_width/3
pricechart_bottom = screen_height/2
car_height = (screen_height/2)/NUM_TEAMS
charge_x = 250
charge_width = 80

player_images = []
for image in player_graphics:
    player_images.append(load_image(image, None, car_height))

backdrop_image = load_image("backdrop.png",screen_width, screen_height)
sticker_image = load_image("sticker.png", None, 400)

font = pygame.font.Font("Quicksand-Regular.ttf", 50)
medium_font = pygame.font.Font("Quicksand-Bold.ttf", 96)
large_font = pygame.font.Font("Quicksand-Bold.ttf", 512)

countdown_numbers = []
for i in range(4):
    countdown_numbers.append(large_font.render(str(i), True, (0,0,0)))

running = True
frame_number = 0

restart_game()

while running:
    screen.fill((255,255,255))
    current_hour = min(23, int(time.time()-start_time))
    take_screenshot = False

    # KEYS & GAME LOGIC
    explodes = []
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == 27:
                running = False
            if event.key == ord("s"):
                take_screenshot = True
            # if event.key == pygame.K_UP:
            #     current_day = (current_day+1) % 365
            # if event.key == pygame.K_DOWN:
            #     current_day = (current_day-1+365) % 365
            if event.key == ord("r"):
                restart_game()
            if event.key == ord(" "):
                if mode == "IDLE":
                    start_countdown()
                if mode == "SCORING":
                    if round < NUM_ROUNDS-1:
                        sounds["anticipation"].set_volume(0.1)
                        sounds["anticipation"].play()
                        round = round + 1
                        mode = "IDLE"
                        reset_charge()

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
                                explodes.append(team) # Register an explode (we don't know position until rendering below) 
                            cash[team] += 7 * (prices[round][current_hour]) / 100 # 7kWh per h, and turn pence into pounds
        if event.type == pygame.QUIT:
            running = False

    # RENDER
    screen.blit(backdrop_image,(0,0))
    screen.blit(sticker_image, (50,100))
    text_surface = font.render("Round "+str(round+1), True, (0,0,0))
    screen.blit(text_surface, (20,0))

    for team in range(NUM_TEAMS):
        spacing = (screen_height/2) / NUM_TEAMS
        top = screen_height/2 + float(team) * spacing
        bottom = screen_height/2 + float(team+1) * spacing

        if team in explodes:
            explode.explode(charge_x+charge_width/2, top, team_colours[team])

        # Car
        if (mode=="FINISHED") and (charge_level[team] < 1.0) and random.random() > 0.5: # Make car flicker if it fails to charge
            pass
        else:
            screen.blit(player_images[team], (50, top)) 
            text_surface = font.render(str(team+1), True, (0,0,0))
            screen.blit(text_surface, (15, top+20))

            # Charge level
            rect_height = spacing-10
            pygame.draw.rect(screen, team_colours[team], pygame.Rect(charge_x,top,charge_width,rect_height), width=1, border_radius=10) 
            pygame.draw.rect(screen, team_colours[team], pygame.Rect(charge_x,top*charge_level[team]+bottom*(1-charge_level[team]),charge_width, rect_height * charge_level[team]), width=0, border_radius=10)

        if mode=="SCORING": # "1st" badge
            if cash[team] <= min(cash):
                image = pygame.image.load("first.png").convert_alpha() 
                scale_factor = (1.0 + 0.2 * sin(time.time()*4)) * (car_height / image.get_height()) 
                scaled_image = pygame.transform.scale(image, ( int(image.get_width() * scale_factor), int(image.get_height() * scale_factor)))
                screen.blit(scaled_image, (150,top))

        # Cash
        text_surface = font.render(f"£{cash[team]:.2f}", True, (0,0,0))
        screen.blit(text_surface, (350, top))

        for hour in range(24):
            colour = None
            if (mode=="PLAY") and (hour==current_hour) and charge_level[team]<1.0:
                if frame_number % 2 == 0:
                    colour = (255,255,0)
            if charging_hours[team][hour]:
                colour = team_colours[team]
            draw_charging_hour(team, hour, colour)

    draw_price_chart(round)

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
            sounds["anticipation"].stop()
            sounds["dnb_loop"].set_volume(0.2)
            sounds["dnb_loop"].play(-1)

    if mode=="PLAY":
        if (time.time() - start_time) > 24:
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
                cash[team] += 0.05 # £1 penalty for each 0.1 of charging not done
                charge_level[team] = min(1.0, charge_level[team] + 0.0025)

        if time.time() > start_time + 5:
            mode = "SCORING"
            start_time = time.time()
            sounds["win"].play()

    if (mode in ["SCORING"]) and (round>=NUM_ROUNDS-1):
        if int(time.time()) % 2:
            text_surface = medium_font.render("GAME OVER", True, (0,0,0))
            screen.blit(text_surface, (screen_width/2 - text_surface.get_width()/2, screen_height/2 - text_surface.get_height()/2))

    explode.render(screen)

    if take_screenshot:
        pygame.image.save(screen, "screenshot.png")
    pygame.display.flip()
    frame_number += 1

# Quit Pygame
pygame.quit()
