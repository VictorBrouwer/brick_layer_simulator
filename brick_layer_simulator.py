import pygame
import sys
import math
from enum import Enum

# Brick and wall dimensions
FULL_BRICK_LENGTH = 210
DRIEKLEZOOR_LENGTH = 155
HALF_BRICK_LENGTH = 100
FULL_BRICK_WIDTH = 100
BRICK_HEIGHT = 50
HEAD_JOINT = 10  # Vertical joint
BED_JOINT = 12.5  # Horizontal joint
COURSE_HEIGHT = BRICK_HEIGHT + BED_JOINT  # 62.5mm

WALL_WIDTH = 2300
WALL_HEIGHT = 2000

STRIDE_WIDTH = 800
STRIDE_HEIGHT = 1300

class BrickType(Enum):
    FULL = 1
    HALF = 2
    DRIEKLEZOOR = 3

class BondType(Enum):
    NORMAL = 1
    FLEMISH = 2

pygame.init()

# Colors
BRICK_COLOR_LIGHT_GREY = (220, 220, 220)
BRICK_COLOR_DARK_GREY = (130, 130, 130)
BACKGROUND_COLOR = (255, 255, 255)

# Stride colors
STRIDE_COLORS = [
    (120, 120, 120),
    (160, 120, 120),  
    (160, 160, 120),  
    (160, 170, 180),  
    (200, 180, 160),  
    (100, 90, 80),   
]

# Scale factor
SCALE = 0.3

# Calculate scaled dimensions
scaled_brick_length = FULL_BRICK_LENGTH * SCALE
scaled_brick_width = FULL_BRICK_WIDTH * SCALE
scaled_half_brick_length = HALF_BRICK_LENGTH * SCALE
scaled_drieklezoor_length = DRIEKLEZOOR_LENGTH * SCALE
scaled_brick_height = BRICK_HEIGHT * SCALE
scaled_head_joint = HEAD_JOINT * SCALE
scaled_bed_joint = BED_JOINT * SCALE
scaled_wall_width = WALL_WIDTH * SCALE
scaled_wall_height = WALL_HEIGHT * SCALE

# Set up display
screen_width = int(scaled_wall_width + 100)
screen_height = int(scaled_wall_height + 100)
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Brick Layer Simulator")

# global variables
built_bricks = []
all_bricks = []
optimized_build_order = []
brick_stride_map = {}
current_bond_type = BondType.NORMAL

def generate_normal_bond(start_x, bottom_y, end_x):
    global all_bricks
    num_layers = int(WALL_HEIGHT / COURSE_HEIGHT)
    
    for layer in range(num_layers):
        # Start from bottom layer and work upwards
        y = bottom_y - (layer + 1) * (scaled_brick_height + scaled_bed_joint)
        # Track real positions (in mm) for determining the strid of a brick
        x_mm = 0
        y_mm = layer * COURSE_HEIGHT
        # Determine if this is an odd or even layer
        is_odd_layer = layer % 2 == 1
        # Calculate the starting x position for this layer
        x = start_x
        layer_bricks = []
        while x < end_x:
            # First check if we need to start with a half brick
            if x == start_x and is_odd_layer:
                brick = {
                    'x': x,
                    'y': y,
                    'width': scaled_half_brick_length,
                    'type': BrickType.HALF,
                    'x_mm': x_mm,
                    'y_mm': y_mm,
                }
                layer_bricks.append(brick)
                x += scaled_half_brick_length + scaled_head_joint
                x_mm += HALF_BRICK_LENGTH + HEAD_JOINT
                
            # Check if we need a half brick at the end
            remaining_width = end_x - x
            remaining_width_mm = WALL_WIDTH - x_mm
            
            if remaining_width < scaled_brick_length:
                # Add a half brick if there's not enough space for a full brick
                if remaining_width >= scaled_half_brick_length:
                    brick = {
                        'x': x,
                        'y': y,
                        'width': scaled_half_brick_length,
                        'type': BrickType.HALF,
                        'x_mm': x_mm,
                        'y_mm': y_mm,
                    }
                    layer_bricks.append(brick)
                    x += scaled_half_brick_length
                    x_mm += HALF_BRICK_LENGTH
                break
                
            # Add a full brick
            brick = {
                'x': x,
                'y': y,
                'width': scaled_brick_length,
                'type': BrickType.FULL,
                'x_mm': x_mm,
                'y_mm': y_mm,
            }
            layer_bricks.append(brick)
            # Move to the next brick position (including head joint)
            x += scaled_brick_length + scaled_head_joint
            x_mm += FULL_BRICK_LENGTH + HEAD_JOINT
        
        all_bricks.append(layer_bricks)


# Even rows: start with DRIEKLEZOOR, then alternate FULL and HALF, end with FULL
# Odd rows: start with FULL, then alternate HALF and FULL, end with DRIEKLEZOOR
def generate_flemish_bond(start_x, bottom_y, end_x):
    global all_bricks
    num_layers = int(WALL_HEIGHT / COURSE_HEIGHT)
    
    for layer in range(num_layers):
        # Start from bottom layer (layer 0) and work upwards
        y = bottom_y - (layer + 1) * (scaled_brick_height + scaled_bed_joint)
        # Track real positions (in mm) for determining the stride of a brick
        x_mm = 0
        y_mm = layer * COURSE_HEIGHT
        # Determine if this is an odd or even layer
        is_odd_layer = layer % 2 == 1
        # Calculate the starting x position for this layer
        x = start_x
        layer_bricks = []
        
        # Keep track of brick count to manage alternating pattern
        brick_count = 0
        
        # Calculate total available width
        available_width = end_x - start_x
        
        # Add bricks until we reach the end
        while x < end_x:
            # First brick in the row
            if brick_count == 0:
                if is_odd_layer:
                    # Odd layer starts with FULL brick
                    brick = {
                        'x': x, 'y': y,
                        'width': scaled_brick_length,
                        'type': BrickType.FULL,
                        'x_mm': x_mm, 'y_mm': y_mm,
                    }
                    x += scaled_brick_length + scaled_head_joint
                    x_mm += FULL_BRICK_LENGTH + HEAD_JOINT
                else:
                    # Even layer starts with DRIEKLEZOOR
                    brick = {
                        'x': x, 'y': y,
                        'width': scaled_drieklezoor_length,
                        'type': BrickType.DRIEKLEZOOR,
                        'x_mm': x_mm, 'y_mm': y_mm,
                    }
                    x += scaled_drieklezoor_length + scaled_head_joint
                    x_mm += DRIEKLEZOOR_LENGTH + HEAD_JOINT
                layer_bricks.append(brick)
                brick_count += 1
                continue

            # Calculate remaining width
            remaining_width = end_x - x
            
            # Handle the end of the row differently based on layer type
            if is_odd_layer:
                # Check if it's the last brick and there's just enough room for the DRIEKLEZOOR at the end
                if remaining_width <= scaled_drieklezoor_length:
                    brick = {
                        'x': x, 'y': y,
                        'width': scaled_drieklezoor_length,
                        'type': BrickType.DRIEKLEZOOR,
                        'x_mm': x_mm, 'y_mm': y_mm,
                    }
                    layer_bricks.append(brick)
                    break
            else:
                # Check if there's just enough room for the FULL brick at the end
                if remaining_width <= scaled_brick_length:
                    brick = {
                        'x': x, 'y': y,
                        'width': scaled_brick_length,
                        'type': BrickType.FULL,
                        'x_mm': x_mm, 'y_mm': y_mm,
                    }
                    layer_bricks.append(brick)
                    break
            
            # In the middle of the row alternate between FULL and HALF
            if is_odd_layer:
                if brick_count % 2 == 1:  # After the first FULL, add HALF
                    brick = {
                        'x': x, 'y': y,
                        'width': scaled_half_brick_length,
                        'type': BrickType.HALF,
                        'x_mm': x_mm, 'y_mm': y_mm,
                    }
                    x += scaled_half_brick_length + scaled_head_joint
                    x_mm += HALF_BRICK_LENGTH + HEAD_JOINT
                else:  # Then add FULL
                    brick = {
                        'x': x, 'y': y,
                        'width': scaled_brick_length,
                        'type': BrickType.FULL,
                        'x_mm': x_mm, 'y_mm': y_mm,
                    }
                    x += scaled_brick_length + scaled_head_joint
                    x_mm += FULL_BRICK_LENGTH + HEAD_JOINT
            else:
                # Even layer alternates between FULL and HALF after DRIEKLEZOOR
                if brick_count % 2 == 1:  # After DRIEKLEZOOR, add FULL
                    brick = {
                        'x': x, 'y': y,
                        'width': scaled_brick_length,
                        'type': BrickType.FULL,
                        'x_mm': x_mm, 'y_mm': y_mm,
                    }
                    x += scaled_brick_length + scaled_head_joint
                    x_mm += FULL_BRICK_LENGTH + HEAD_JOINT
                else:  # Then add HALF
                    brick = {
                        'x': x, 'y': y,
                        'width': scaled_half_brick_length,
                        'type': BrickType.HALF,
                        'x_mm': x_mm, 'y_mm': y_mm,
                    }
                    x += scaled_half_brick_length + scaled_head_joint
                    x_mm += HALF_BRICK_LENGTH + HEAD_JOINT
            
            layer_bricks.append(brick)
            brick_count += 1
        
        all_bricks.append(layer_bricks)

def generate_wall_layout():
    global all_bricks
    all_bricks = []  # Clear any existing bricks
    
    # Start position
    start_x = (screen_width - scaled_wall_width) / 2
    bottom_y = screen_height - 50
    end_x = start_x + scaled_wall_width
    
    if current_bond_type == BondType.NORMAL:
        generate_normal_bond(start_x, bottom_y, end_x)
    elif current_bond_type == BondType.FLEMISH:
        generate_flemish_bond(start_x, bottom_y, end_x)
    
    # After creating the wall layout, we need to optimize the build order
    calculate_build_order()

#calulate which stride each brick belongs to and sort the bricks in the build order
def calculate_build_order():
    global optimized_build_order, brick_stride_map
    optimized_build_order = []  # Clear existing build order
    brick_stride_map = {}  # Clear existing stride map

    horizontal_strides = math.ceil(WALL_WIDTH / STRIDE_WIDTH)
    vertical_strides = math.ceil(WALL_HEIGHT / STRIDE_HEIGHT)
    # Group bricks by stride in dictionary
    stride_bricks = {}
    
    # Assign bricks to strides
    for layer in all_bricks:
        for brick in layer:
            # Calculate stride for each brick based on mm positions
            brickwidth_mm = brick['width'] / SCALE
            x_stride = int((brick['x_mm'] + brickwidth_mm / 2) / STRIDE_WIDTH)
            y_stride = int((brick['y_mm'] + COURSE_HEIGHT / 2) / STRIDE_HEIGHT)
            stride_key = (x_stride, y_stride)
            
            if stride_key not in stride_bricks:
                stride_bricks[stride_key] = []
            
            stride_bricks[stride_key].append(brick)
            
            # Create a dictionary to map each brick to its stride for coloring
            stride_index = y_stride * horizontal_strides + x_stride
            brick_key = (brick['x_mm'], brick['y_mm'])
            brick_stride_map[brick_key] = stride_index
    
    # Build the optimized order by iterating through strides from bottom to top and left to right
    for v in range(vertical_strides):
        for h in range(horizontal_strides):
            stride_key = (h, v)
            if stride_key in stride_bricks:
                # Sort bricks within this stride
                stride_group = stride_bricks[stride_key]
                # sort by horizontal position
                stride_group.sort(key=lambda b: b['x_mm'])
                # Sort by vertical position
                stride_group.sort(key=lambda b: b['y_mm'])
                # Append the sorted bricks to the optimized build order
                optimized_build_order.extend(stride_group)

def draw_wall():
    # Draw all bricks
    for layer in all_bricks:
        for brick in layer:
            if brick in built_bricks:
                # Use the stride color for built bricks
                brick_key = (brick['x_mm'], brick['y_mm'])
                stride_index = brick_stride_map.get(brick_key)
                color = STRIDE_COLORS[stride_index]
            else:
                color = BRICK_COLOR_LIGHT_GREY
            # Draw the brick
            pygame.draw.rect(
                screen,
                color,
                (brick['x'], brick['y'], brick['width'], scaled_brick_height)
            )

def build_next_brick():
    global built_bricks
    
    # Find the next unbuilt brick
    for brick in optimized_build_order:
        if brick not in built_bricks:
            built_bricks.append(brick)
            return True
    return False

def switch_bond_type():
    global current_bond_type, built_bricks
    
    if current_bond_type == BondType.NORMAL:
        current_bond_type = BondType.FLEMISH
    else:
        current_bond_type = BondType.NORMAL
    
    # Reset the built bricks
    built_bricks = []
    
    # Regenerate the wall layout
    generate_wall_layout()

def main():
    generate_wall_layout()
    
    # Initialize font
    font = pygame.font.SysFont(None, 24)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:  # ENTER key
                    build_next_brick()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:  # SPACE key
                    switch_bond_type()
        
        # First clear the screen
        screen.fill(BACKGROUND_COLOR)
        # Draw the wall
        draw_wall()
        
        # Display current bond type and controls
        bond_type_string = f"Current Bond: {'NORMAL' if current_bond_type == BondType.NORMAL else 'FLEMISH'}"
        bond_text = font.render(bond_type_string, True, (0, 0, 0))
        screen.blit(bond_text, (10, 10))
        controls_surface = font.render("Controls: ENTER = add brick, SPACE = switch bond", True, (0, 0, 0))
        screen.blit(controls_surface, (10, screen_height - 30))
        
        # Update the display
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main() 
