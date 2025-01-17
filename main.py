import pygame
import time
import random
from datetime import date
from PIL import Image, ImageEnhance
from math import sin
import sys, os
import explode

NUM_TEAMS = 5
NUM_ROUNDS = 5
CHARGING_HOURS = 12

pygame.init()
displays = pygame.display.get_desktop_sizes()
print("Displays:\n",displays)

display = 0
if len(sys.argv) > 1:
    display = int(sys.argv[1])
print("Using display",display)
(screen_width, screen_height) = displays[display]
screen = pygame.display.set_mode((screen_width, screen_height), display=display, flags=pygame.FULLSCREEN | pygame.SCALED)
pygame.key.set_repeat(500, 50)  # 500ms delay, 50ms interval
pygame.mixer.init()
pygame.mouse.set_visible(False)

start_charge_level = [
        0.5,
        0.5,
        0.3,
        0.3,
        0
        ]

prices = [ # Pence per kWh. 24h per round.
        [10,10,11,12,13,13,17,20,23,26,25,25],
        [18,19,18,17,10,10, 9,10,12,14,15,16],
        [20,20,19,14, 9,14,10, 7,17,17,19,21],
        [10, 9, 8, 6, 3, 0,-3,-4, 4,10,12,14],
        [20,20,23,24,26,26,24,20,16, 9, 3, 0]
        ]

player_graphics = ["red_walking_robot.png", "green_sphere_robot.png", "blue_wheeled_robot.png", "orange_wheeled_robot.png", "pink_tracked_robot.png"]
player_names = ["ben", "bob", "mia", "kay", "sam"]

team_colours = [
        (255,0,0),
        (0,255,0),
        (0,0,255),
        (255,165,0),
        (255,192,203)
        ]

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

def draw_price_chart(day, highlight_hour, do_highlight):
    def draw_hour_range(start,len,colour):
        points = []
        for hour in range(start, start+len):
            x = pricechart_left + hour * xscale
            y = pricechart_bottom - prices[day][hour] * yscale
            points.append( (x,y) )
            points.append( (x + xscale, y) )
        pygame.draw.lines(screen, colour, False, points, 8) 
    pygame.draw.line(screen, (128,128,128), (pricechart_left, 0), (pricechart_left, pricechart_bottom), 2)
    pygame.draw.line(screen, (128,128,128), (pricechart_left, pricechart_bottom), (screen_width, pricechart_bottom), 2)
    pygame.draw.line(screen, (128,128,128), (screen_width, pricechart_bottom), (screen_width, 0), 2)
    pygame.draw.line(screen, (128,128,128), (screen_width, 0), (pricechart_left, 0), 2)
    text_surface = font.render("Price Chart", True, (0,0,0))
    screen.blit(text_surface, (pricechart_left + 20, 0))
    wid = screen_width - pricechart_left
    hgt = pricechart_bottom
    xscale = wid/CHARGING_HOURS
    yscale = pricechart_bottom / 27 # 27p is max price
    draw_hour_range(0,CHARGING_HOURS, (255,64,64))
    if do_highlight:
        draw_hour_range(highlight_hour, 1,(255,255,0))

def draw_charging_hour(team, hour, fill):
    lines = []
    left = pricechart_left
    top = pricechart_bottom
    xscale = (screen_width - pricechart_left) / CHARGING_HOURS
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
        scaled_image = pygame.transform.smoothscale(image, ( int(image.get_width() * scale_factor), int(image.get_height() * scale_factor)))
    else:
        scaled_image = pygame.transform.smoothscale(image, (target_width, target_height))
    return scaled_image

def start_countdown():
    global mode, start_time
    mode = "COUNTDOWN"
    start_time = time.time()
    sounds["ready"].play()
    sounds["anticipation"].set_volume(0.1)
    sounds["anticipation"].play()

def reset_charge(round):
    global charge_level, charging_hours
    charge_level = [start_charge_level[round] for i in range(NUM_TEAMS)]
    charging_hours = [[False for __ in range(CHARGING_HOURS)] for _ in range(NUM_TEAMS)]

def restart_game(): 
    global round, cash, mode, start_time, charge_level, charging_hours
    round = 0
    cash = [0.00 for i in range(NUM_TEAMS)]

    # start_countdown()
    mode = "IDLE"
    start_time = time.time()
    reset_charge(round)

    sounds["dnb_loop"].stop()

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
battery_image = load_image("battery.png",None, 50)

font = pygame.font.Font("Quicksand-Regular.ttf", 50)
medium_font = pygame.font.Font("Quicksand-Bold.ttf", 96)
large_font = pygame.font.Font("Quicksand-Bold.ttf", 512)
tiny_font = pygame.font.Font("Quicksand-Bold.ttf", 20)

countdown_numbers = []
for i in range(4):
    countdown_numbers.append(large_font.render(str(i), True, (0,0,0)))

running = True
frame_number = 0

restart_game()

while running:
    screen.fill((255,255,255))
    current_hour = min(CHARGING_HOURS-1, int(time.time()-start_time))
    take_screenshot = False

    # KEYS & GAME LOGIC
    explodes = []
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == 27:
                running = False
            if event.key == ord("s"):
                take_screenshot = True
            if event.key == pygame.K_UP:
                if round < NUM_ROUNDS-1:
                    round += 1
            if event.key == pygame.K_DOWN:
                if round > 0:
                    round -= 1
            if event.key == ord("r"):
                restart_game()
            if event.key == ord(" "):
                if mode == "IDLE":
                    start_countdown()
                if mode == "SCORING":
                    if round < NUM_ROUNDS-1:
                        round = round + 1
                        mode = "IDLE"
                        reset_charge(round)

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
    screen.blit(sticker_image, (40,80))
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
            text_surface = font.render(str(team+1), True, (0,0,0))
            screen.blit(text_surface, (15, top+10))  # Team number
            x = 70
            if mode not in ["COUNTDOWN", "PLAY"]:
                x += sin(time.time() + team*2) * 20
            screen.blit(player_images[team], (x, top))  # Team image
            text_surface = tiny_font.render(player_names[team], True, (0,0,0)) # Team Name
            screen.blit(text_surface, (10, top+spacing/2+10)) 

            # Charge level
            rect_height = spacing-10
            pygame.draw.rect(screen, team_colours[team], pygame.Rect(charge_x,top,charge_width,rect_height), width=1, border_radius=10) 
            pygame.draw.rect(screen, team_colours[team], pygame.Rect(charge_x,top*charge_level[team] + (top+rect_height)*(1-charge_level[team]),charge_width, rect_height * charge_level[team]), width=0, border_radius=10)
            screen.blit(battery_image, (charge_x + charge_width/2 - battery_image.get_width()/2, top + rect_height/2 - battery_image.get_height()/2))

        if mode=="SCORING": # "1st" badge
            if cash[team] <= min(cash):
                image = pygame.image.load("first.png").convert_alpha() 
                scale_factor = (1.0 + 0.2 * sin(time.time()*4)) * (car_height / image.get_height()) 
                scaled_image = pygame.transform.smoothscale(image, ( int(image.get_width() * scale_factor), int(image.get_height() * scale_factor)))
                screen.blit(scaled_image, (150,top))

        # Cash
        text_surface = font.render(f"£{cash[team]:.2f}", True, (0,0,0))
        screen.blit(text_surface, (350, top+10))

        for hour in range(CHARGING_HOURS):
            colour = None
            if (mode=="PLAY") and (hour==current_hour) and charge_level[team]<1.0:
                if frame_number % 2 == 0:
                    colour = (255,255,0)
            if charging_hours[team][hour]:
                colour = team_colours[team]
            draw_charging_hour(team, hour, colour)

    draw_price_chart(round, current_hour, mode=="PLAY")

    if mode=="COUNTDOWN":
        t = time.time() - start_time
        if t < 3:
            i = int(t)
            ts = t % 1
            scale = (screen_height) / (1 + ts)
            c = pygame.transform.smoothscale(countdown_numbers[3-i], (scale,scale))
            c.set_alpha(128)
            screen.blit(c, (screen_width/2 - scale/2, screen_height/2 - scale/2))
        else:
            mode = "PLAY"
            start_time = time.time()
            sounds["anticipation"].stop()
            sounds["dnb_loop"].set_volume(0.2)
            sounds["dnb_loop"].play(-1)

    if mode=="PLAY":
        if (time.time() - start_time) > CHARGING_HOURS:
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
                cash[team] += 0.04 # £1 penalty for each 0.1 of charging not done
                charge_level[team] = min(1.0, charge_level[team] + 0.002)

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
