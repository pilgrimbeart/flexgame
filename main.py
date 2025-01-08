import pygame
from datetime import date
from PIL import Image, ImageEnhance

NUM_TEAMS = 3

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

charging_hours = [[False for __ in range(24)] for _ in range(NUM_TEAMS)]
def draw_charging_hour(team, hour, charging):
    lines = []
    left = screen_width / 2
    top = screen_height / 2
    xscale = (screen_width / 2 ) / 24
    yscale = (screen_height / 2) / NUM_TEAMS
    lines.append( (left + hour * xscale, top + team * yscale) )
    lines.append( (left + (hour+1) * xscale, top + team * yscale) )
    lines.append( (left + (hour+1) * xscale, top + (team+1) * yscale) )
    lines.append( (left + hour * xscale, top + (team+1) * yscale) )
    pygame.draw.lines(screen, (64,64,64), True, lines, 1)

car_images = []
def load_car_image(imagename):
    global car_images
    image = pygame.image.load(imagename).convert_alpha()  # Maintain transparency
    scale_factor = car_height / image.get_height() 
    scaled_image = pygame.transform.scale(image, ( int(image.get_width() * scale_factor), int(image.get_height() * scale_factor)))
    car_images.append(scaled_image)

read_energy_prices()

pygame.init()
pygame.mixer.init()
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

sound = pygame.mixer.Sound("drum-and-bass-drums-loop-160-bpm-1-131244.mp3")
sound.play(-1)
sound2 = pygame.mixer.Sound("ready-fight-37973.mp3")
sound2.play()
current_day = 0
running = True
while running:
    screen.fill((255,255,255))

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == 27:
                running = False
            if event.key == pygame.K_UP:
                current_day = (current_day+1) % 365
            if event.key == pygame.K_DOWN:
                current_day = (current_day-1+365) % 365
        if event.type == pygame.QUIT:
            running = False

    for team in range(3):
        screen.blit(car_images[team], (0, screen_height - team*car_height))

    for team in range(NUM_TEAMS):
        for hour in range(24):
            draw_charging_hour(team, hour, charging_hours[team][hour])

    text_surface = font.render("Day "+str(current_day), True, (0,0,0))
    screen.blit(text_surface, (0,0))
    draw_price_chart(current_day)

    pygame.display.flip()

# Quit Pygame
pygame.quit()
