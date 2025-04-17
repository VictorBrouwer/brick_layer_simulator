import pygame
import sys
import math
from enum import Enum
from typing import List, Tuple, Dict

# Brick and wall specifications (in mm)
FULL_BRICK_LENGTH = 210
FULL_BRICK_WIDTH = 100
HALF_BRICK_LENGTH = 100
BRICK_HEIGHT = 50
HEAD_JOINT = 10  # Vertical joint
BED_JOINT = 12.5  # Horizontal joint
COURSE_HEIGHT = BRICK_HEIGHT + BED_JOINT  # 62.5mm

# Wall dimensions
WALL_WIDTH = 2300
WALL_HEIGHT = 2000

# Robot constraints
STRIDE_WIDTH = 800
STRIDE_HEIGHT = 1300

class BrickType(Enum):
    FULL = 1
    HALF = 2

pygame.init()

# Colors
# BRICK_COLOR = (178, 34, 34)  # Brick red
# MORTAR_COLOR = (169, 169, 169)  # Grey
BRICK_COLOR_LIGHT_GREY = (169, 169, 169) # Brick grey
BRICK_COLOR_DARK_GREY = (180, 180, 180) # Brick grey
BACKGROUND_COLOR = (255, 255, 255)  # White

# Scale factor (to convert mm to pixels)
SCALE = 0.3  # Adjust this value to make visualization larger or smaller

# Calculate scaled dimensions
scaled_brick_length = FULL_BRICK_LENGTH * SCALE
scaled_brick_width = FULL_BRICK_WIDTH * SCALE
scaled_half_brick_length = HALF_BRICK_LENGTH * SCALE
scaled_brick_height = BRICK_HEIGHT * SCALE
scaled_head_joint = HEAD_JOINT * SCALE
scaled_bed_joint = BED_JOINT * SCALE
scaled_wall_width = WALL_WIDTH * SCALE
scaled_wall_height = WALL_HEIGHT * SCALE

# Set up display
screen_width = int(scaled_wall_width + 100)  # Add some margin
screen_height = int(scaled_wall_height + 100)  # Add some margin
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Brick Layer Simulator")

def draw_wall():
    """Draw the stretcher bond wall pattern."""
    screen.fill(BACKGROUND_COLOR)
    
    # Calculate number of courses (rows of bricks)
    num_layers = int(WALL_HEIGHT / COURSE_HEIGHT)
    
    # Start position (centered horizontally, at bottom of screen vertically)
    start_x = (screen_width - scaled_wall_width) / 2
    # Position at bottom of screen with 50px margin
    bottom_y = screen_height - 50
    end_x = start_x + scaled_wall_width
    
    for layer in range(num_layers):
        # Start from bottom layer (layer 0) and work upwards. Higher layer= higher up the wall
        y = bottom_y - (layer + 1) * (scaled_brick_height + scaled_bed_joint)
        
        # Determine if this is an odd or even layer
        is_odd_layer = layer % 2 == 1
        
        # Calculate the starting x position for this layer (with offset for odd layers)
        x = start_x
        
        # Draw bricks for this layer
        while x < end_x:
            # first check if we need tostart with a half brick
            if x == start_x and is_odd_layer:
                pygame.draw.rect(
                    screen, 
                    BRICK_COLOR_LIGHT_GREY, 
                    (x, y, scaled_half_brick_length, scaled_brick_height)
                )
                x += scaled_half_brick_length + scaled_head_joint
                
            # Check if we need a half brick at the end
            remaining_width = end_x - x            
            if remaining_width < scaled_brick_length:
                # Draw a half brick if there's not enough space for a full brick
                if remaining_width >= scaled_half_brick_length:
                    pygame.draw.rect(
                        screen, 
                        BRICK_COLOR_LIGHT_GREY, 
                        (x, y, scaled_half_brick_length, scaled_brick_height)
                    )
                break
                
            # Draw a full brick
            pygame.draw.rect(
                screen, 
                BRICK_COLOR_LIGHT_GREY, 
                (x, y, scaled_brick_length, scaled_brick_height)
            )
            
            # Move to the next brick position (including head joint)
            x += scaled_brick_length + scaled_head_joint

def main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        draw_wall()
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main() 
