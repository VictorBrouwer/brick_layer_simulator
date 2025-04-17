import pygame
import sys
import math
from enum import Enum
from typing import List, Tuple, Dict

# Brick and wall specifications
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
BRICK_COLOR_LIGHT_GREY = (220, 220, 220)  # Light grey for unbuilt bricks
BRICK_COLOR_DARK_GREY = (130, 130, 130)   # Dark grey for built bricks
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

# global variables
built_bricks = []
all_bricks = []

def generate_wall_layout():
    # use global to get modify the all bricks list
    global all_bricks
    all_bricks = []
    
    # Calculate number of layers
    num_layers = int(WALL_HEIGHT / COURSE_HEIGHT)
    
    # Start position
    start_x = (screen_width - scaled_wall_width) / 2
    bottom_y = screen_height - 50
    end_x = start_x + scaled_wall_width
    
    for layer in range(num_layers):
        # Start from bottom layer (layer 0) and work upwards
        y = bottom_y - (layer + 1) * (scaled_brick_height + scaled_bed_joint)
        
        # Determine if this is an odd or even layer
        is_odd_layer = layer % 2 == 1
        
        # Calculate the starting x position for this layer
        x = start_x
        layer_bricks = []
        
        # Add bricks for this layer
        while x < end_x:
            # First check if we need to start with a half brick
            if x == start_x and is_odd_layer:
                layer_bricks.append({
                    'x': x,
                    'y': y,
                    'width': scaled_half_brick_length,
                    'height': scaled_brick_height,
                    'type': BrickType.HALF
                })
                x += scaled_half_brick_length + scaled_head_joint
                
            # Check if we need a half brick at the end
            remaining_width = end_x - x            
            if remaining_width < scaled_brick_length:
                # Add a half brick if there's not enough space for a full brick
                if remaining_width >= scaled_half_brick_length:
                    layer_bricks.append({
                        'x': x,
                        'y': y,
                        'width': scaled_half_brick_length,
                        'height': scaled_brick_height,
                        'type': BrickType.HALF
                    })
                    x += scaled_half_brick_length
                break
                
            # Add a full brick
            layer_bricks.append({
                'x': x,
                'y': y,
                'width': scaled_brick_length,
                'height': scaled_brick_height,
                'type': BrickType.FULL
            })
            
            # Move to the next brick position (including head joint)
            x += scaled_brick_length + scaled_head_joint
        
        all_bricks.append(layer_bricks)

def draw_wall():
    screen.fill(BACKGROUND_COLOR)
    
    # Draw all bricks
    for layer in all_bricks:
        for brick in layer:
            # Determine if this brick has been built
            is_built = brick in built_bricks
            if is_built:
                color = BRICK_COLOR_DARK_GREY
            else:
                color = BRICK_COLOR_LIGHT_GREY
            
            # Draw the brick
            pygame.draw.rect(
                screen,
                color,
                (brick['x'], brick['y'], brick['width'], brick['height'])
            )

def build_next_brick():
    """Build the next brick in the wall"""
    # use global to get modify the built bricks list
    global built_bricks
    
    # Find the next brick to build (start from bottom left)
    for layer in (all_bricks):
        for brick in layer:
            if brick not in built_bricks:
                built_bricks.append(brick)
                return True
    
    return False  # No more bricks to build

def main():
    # Generate the complete wall layout
    generate_wall_layout()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:  # ENTER key
                    build_next_brick()
        
        draw_wall()
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main() 
