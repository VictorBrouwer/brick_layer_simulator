import pygame
import sys
import math
import random
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
    WILD = 3

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
joint_positions = {}  # Changed to dictionary with layer as key
current_bond_type = BondType.NORMAL

def create_brick(x, y, x_mm, y_mm, brick_type):
    if brick_type == BrickType.FULL:
        width = scaled_brick_length
    elif brick_type == BrickType.HALF:
        width = scaled_half_brick_length
    elif brick_type == BrickType.DRIEKLEZOOR:
        width = scaled_drieklezoor_length
    
    return {
        'x': x,
        'y': y,
        'width': width,
        'type': brick_type,
        'x_mm': x_mm,
        'y_mm': y_mm,
    }

def update_positions(x, x_mm, brick_type, add_joint=True):
    if brick_type == BrickType.FULL:
        x_increment = scaled_brick_length
        x_mm_increment = FULL_BRICK_LENGTH
    elif brick_type == BrickType.HALF:
        x_increment = scaled_half_brick_length
        x_mm_increment = HALF_BRICK_LENGTH
    elif brick_type == BrickType.DRIEKLEZOOR:
        x_increment = scaled_drieklezoor_length
        x_mm_increment = DRIEKLEZOOR_LENGTH
    
    # Add joint if needed
    if add_joint:
        x_increment += scaled_head_joint
        x_mm_increment += HEAD_JOINT
    
    return x + x_increment, x_mm + x_mm_increment

def generate_bond_layer(start_x, bottom_y, end_x, layer, bond_type):
    global joint_positions
    # Create a new entry for this layer if it doesn't exist
    if layer not in joint_positions:
        joint_positions[layer] = []
    else:
        joint_positions[layer] = []  # Reset layer joints
    
    # Calculate position values
    y = bottom_y - (layer + 1) * (scaled_brick_height + scaled_bed_joint)
    x_mm = 0
    y_mm = layer * COURSE_HEIGHT
    is_odd_layer = layer % 2 == 1
    x = start_x
    
    layer_bricks = []
    
    if bond_type == BondType.NORMAL:
        # Normal bond pattern
        # For odd layers, start with half brick
        if is_odd_layer and x == start_x:
            brick = create_brick(x, y, x_mm, y_mm, BrickType.HALF)
            layer_bricks.append(brick)
            x, x_mm = update_positions(x, x_mm, BrickType.HALF)
            
        # Add full bricks until we reach the end
        while x < end_x:
            remaining_width = end_x - x
            
            # Handle end of row
            if remaining_width < scaled_brick_length:
                if remaining_width >= scaled_half_brick_length:
                    brick = create_brick(x, y, x_mm, y_mm, BrickType.HALF)
                    layer_bricks.append(brick)
                break
                
            # Add a full brick
            brick = create_brick(x, y, x_mm, y_mm, BrickType.FULL)
            layer_bricks.append(brick)
            x, x_mm = update_positions(x, x_mm, BrickType.FULL)
    
    elif bond_type == BondType.FLEMISH:
        # Flemish bond pattern
        brick_count = 0
        
        while x < end_x:
            # First brick in row
            if brick_count == 0:
                if is_odd_layer:
                    # Odd layer starts with FULL brick
                    brick = create_brick(x, y, x_mm, y_mm, BrickType.FULL)
                    layer_bricks.append(brick)
                    x, x_mm = update_positions(x, x_mm, BrickType.FULL)
                else:
                    # Even layer starts with DRIEKLEZOOR
                    brick = create_brick(x, y, x_mm, y_mm, BrickType.DRIEKLEZOOR)
                    layer_bricks.append(brick)
                    x, x_mm = update_positions(x, x_mm, BrickType.DRIEKLEZOOR)
                brick_count += 1
                continue
            
            # Calculate remaining width
            remaining_width = end_x - x
            
            # Handle end of row
            if is_odd_layer:
                # Check if it's the last brick and there's just enough room for the DRIEKLEZOOR at the end
                if remaining_width <= scaled_drieklezoor_length:
                    brick = create_brick(x, y, x_mm, y_mm, BrickType.DRIEKLEZOOR)
                    layer_bricks.append(brick)
                    break
            else:
                # Check if there's just enough room for the FULL brick at the end
                if remaining_width <= scaled_brick_length:
                    brick = create_brick(x, y, x_mm, y_mm, BrickType.FULL)
                    layer_bricks.append(brick)
                    break
            
            # Middle of row - alternating patterns
            if is_odd_layer:
                if brick_count % 2 == 1:  # After the first FULL, add HALF
                    brick = create_brick(x, y, x_mm, y_mm, BrickType.HALF)
                    layer_bricks.append(brick)
                    x, x_mm = update_positions(x, x_mm, BrickType.HALF)
                else:  # Then add FULL
                    brick = create_brick(x, y, x_mm, y_mm, BrickType.FULL)
                    layer_bricks.append(brick)
                    x, x_mm = update_positions(x, x_mm, BrickType.FULL)
            else:
                if brick_count % 2 == 1:  # After DRIEKLEZOOR, add FULL
                    brick = create_brick(x, y, x_mm, y_mm, BrickType.FULL)
                    layer_bricks.append(brick)
                    x, x_mm = update_positions(x, x_mm, BrickType.FULL)
                else:  # Then add HALF
                    brick = create_brick(x, y, x_mm, y_mm, BrickType.HALF)
                    layer_bricks.append(brick)
                    x, x_mm = update_positions(x, x_mm, BrickType.HALF)
            
            brick_count += 1
    
    elif bond_type == BondType.WILD:
        # Wild bond pattern
        brick_count = 0
        consecutive_full_bricks = 0
        consecutive_half_bricks = 0
        
        while x < end_x:
            # First brick in row - corners have special rules
            if brick_count == 0:
                if is_odd_layer:
                    # Odd layer starts with HALF brick
                    brick = create_brick(x, y, x_mm, y_mm, BrickType.HALF)
                    layer_bricks.append(brick)
                    x, x_mm = update_positions(x, x_mm, BrickType.HALF)
                    consecutive_half_bricks = 1
                    consecutive_full_bricks = 0
                    # Store the joint position at the end of this brick
                    joint_positions[layer].append(x_mm - HEAD_JOINT)
                else:
                    # Even layer starts with DRIEKLEZOOR
                    brick = create_brick(x, y, x_mm, y_mm, BrickType.DRIEKLEZOOR)
                    layer_bricks.append(brick)
                    x, x_mm = update_positions(x, x_mm, BrickType.DRIEKLEZOOR)
                    consecutive_half_bricks = 0
                    consecutive_full_bricks = 0
                    # Store the joint position at the end of this brick
                    joint_positions[layer].append(x_mm - HEAD_JOINT)
                brick_count += 1
                continue
            
            # Calculate remaining width
            remaining_width = end_x - x
            
            # Handle end of row
            if remaining_width < scaled_brick_length:
                # If we're near the end, place the appropriate ending brick
                if is_odd_layer:
                    # Odd layer (starting with half) should end with drieklezoor if there's room
                    if remaining_width >= scaled_drieklezoor_length:
                        brick = create_brick(x, y, x_mm, y_mm, BrickType.DRIEKLEZOOR)
                        layer_bricks.append(brick)
                        # Store the joint position at the end of this brick
                        joint_positions[layer].append(x_mm + DRIEKLEZOOR_LENGTH)
                else:
                    # Even layer (starting with drieklezoor) should end with half brick if there's room
                    if remaining_width >= scaled_half_brick_length:
                        brick = create_brick(x, y, x_mm, y_mm, BrickType.HALF)
                        layer_bricks.append(brick)
                        # Store the joint position at the end of this brick
                        joint_positions[layer].append(x_mm + HALF_BRICK_LENGTH)
                break
            
            # Decide whether to use a full or half brick based on rules
            use_full_brick = False
            
            # Check consecutive brick types - these are primary rules
            if consecutive_half_bricks >= 3:
                # Rule: max 3 half bricks in a row
                use_full_brick = True
            elif consecutive_full_bricks >= 5:
                # Rule: max 5 full bricks in a row
                use_full_brick = False
            else:
                # Calculate the potential joint positions for both brick types
                full_joint_pos = x_mm + FULL_BRICK_LENGTH
                half_joint_pos = x_mm + HALF_BRICK_LENGTH
                
                # Check for vertical staggered patterns (falling teeth pattern across layers)
                full_pattern_length = 0
                half_pattern_length = 0
                
                # We need to check if either joint position would continue a vertical pattern
                if layer > 0:  # Only check if we have previous layers
                    # Look for patterns in both potential brick placements
                    full_pattern_length = check_vertical_pattern(layer, full_joint_pos)
                    half_pattern_length = check_vertical_pattern(layer, half_joint_pos)
                
                # If either pattern is too long (6 or more), avoid extending it
                if (full_pattern_length > 6) and (half_pattern_length > 6):
                    print("Pattern too long for both full and half brick in layer", layer)
                    print("at brick number", brick_count)
                if full_pattern_length >= 6:
                    use_full_brick = False  # Avoid extending the pattern with full brick
                elif half_pattern_length >= 6:
                    use_full_brick = True   # Avoid extending the pattern with half brick
                else:
                    # If no pattern concerns, randomly choose with slight preference for full bricks
                    use_full_brick = random.random() < 0.6
            
            # Create the appropriate brick
            if use_full_brick:
                brick = create_brick(x, y, x_mm, y_mm, BrickType.FULL)
                layer_bricks.append(brick)
                next_joint_pos = x_mm + FULL_BRICK_LENGTH
                x, x_mm = update_positions(x, x_mm, BrickType.FULL)
                consecutive_full_bricks += 1
                consecutive_half_bricks = 0
            else:
                brick = create_brick(x, y, x_mm, y_mm, BrickType.HALF)
                layer_bricks.append(brick)
                next_joint_pos = x_mm + HALF_BRICK_LENGTH
                x, x_mm = update_positions(x, x_mm, BrickType.HALF)
                consecutive_half_bricks += 1
                consecutive_full_bricks = 0
            
            # Store the joint position
            joint_positions[layer].append(next_joint_pos)
            
            brick_count += 1
    
    return layer_bricks

# Helper function to check for vertical staggered patterns
def check_vertical_pattern(current_layer, joint_pos):
    # Check for falling teeth pattern
    teeth_pattern_length = check_pattern_type(current_layer, joint_pos, "falling_teeth")
    if teeth_pattern_length > 6:
        print("Pattern too long for falling teeth",)
    
    # Check for staggering left pattern
    left_pattern_length = check_pattern_type(current_layer, joint_pos, "staggering_left")
    if left_pattern_length > 6:
        print("Pattern too long for staggering left",)
    
    # Check for staggering right pattern
    right_pattern_length = check_pattern_type(current_layer, joint_pos, "staggering_right")
    if right_pattern_length > 6:
        print("Pattern too long for staggering right",)
    
    # Return the longest pattern found

    return max(teeth_pattern_length, left_pattern_length, right_pattern_length)

def check_pattern_type(current_layer, joint_pos, pattern_type):
    # The offset distance we're looking for between layers
    vertical_offset = 55
    max_offset_tolerance = 10  # How much variation we allow
    
    pattern_length = 0
    current_pos = joint_pos
    
    # For falling teeth pattern, we need to track both positions in the alternating pattern
    original_pos = joint_pos
    offset_pos = None  # Will be set when we find the first offset position
    
    # Start checking from the current_layer downward
    for layer_id in range(current_layer-1, -1, -1):
        if layer_id not in joint_positions:
            break
            
        found_match = False
        
        for joint in joint_positions[layer_id]:
            offset = joint - current_pos  # Positive = right, negative = left
            
            if pattern_type == "falling_teeth":
                layer_offset = current_layer - layer_id
                
                if layer_offset % 2 == 0:
                    # Even offset - should align with original position
                    if abs(joint - original_pos) <= max_offset_tolerance:
                        found_match = True
                        current_pos = joint
                        break
                else:
                    # Odd offset - should be at the offset position
                    if offset_pos is None:
                        # First time we've encountered an odd layer
                        # Calculate how far this is from the original position
                        if abs(abs(joint - original_pos) - vertical_offset) <= max_offset_tolerance:
                            offset_pos = joint  # Remember this position for future odd layers
                            found_match = True
                            current_pos = joint
                            break
                    else:
                        # Check if this odd layer aligns with previous odd layers
                        if abs(joint - offset_pos) <= max_offset_tolerance:
                            found_match = True
                            current_pos = joint
                            break
                    
            elif pattern_type == "staggering_left":
                # For staggering left, we want negative offset (around -55mm)
                if abs(offset + vertical_offset) <= max_offset_tolerance:
                    found_match = True
                    current_pos = joint
                    break
                    
            elif pattern_type == "staggering_right":
                # For staggering right, we want positive offset (around +55mm)
                if abs(offset - vertical_offset) <= max_offset_tolerance:
                    found_match = True
                    current_pos = joint
                    break
        
        if found_match:
            pattern_length += 1
        else:
            break
    
    # For falling teeth pattern, we need at least 3 layers to confirm the pattern
    if pattern_type == "falling_teeth" and pattern_length < 2:
        return 0
        
    return pattern_length

def generate_wall():
    global all_bricks
    all_bricks = []  # Clear any existing bricks
    
    # Start position
    start_x = (screen_width - scaled_wall_width) / 2
    bottom_y = screen_height - 50
    end_x = start_x + scaled_wall_width
    
    # Calculate number of layers
    num_layers = int(WALL_HEIGHT / COURSE_HEIGHT)
    
    # Generate each layer
    for layer in range(num_layers):
        layer_bricks = generate_bond_layer(start_x, bottom_y, end_x, layer, current_bond_type)
        all_bricks.append(layer_bricks)
    
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
            x_stride = int((brick['x_mm'] + (brickwidth_mm / 2)) / STRIDE_WIDTH)
            y_stride = int((brick['y_mm'] + (COURSE_HEIGHT / 2)) / STRIDE_HEIGHT)
            stride_key = (x_stride, y_stride)
            
            if stride_key not in stride_bricks:
                stride_bricks[stride_key] = []
            
            stride_bricks[stride_key].append(brick)
            
            # Create a dictionary to map each brick to its stride for coloring
            stride_index = y_stride * horizontal_strides + x_stride
            brick_key = (brick['x_mm'], brick['y_mm'])
            brick_stride_map[brick_key] = stride_index % len(STRIDE_COLORS)
    
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
                stride_index = brick_stride_map.get(brick_key, 0)
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
    global current_bond_type, built_bricks, joint_positions
    
    if current_bond_type == BondType.NORMAL:
        current_bond_type = BondType.FLEMISH
    elif current_bond_type == BondType.FLEMISH:
        current_bond_type = BondType.WILD
    else:
        current_bond_type = BondType.NORMAL
    
    # Reset the built bricks and joint positions
    built_bricks = []
    joint_positions = {}
    generate_wall()

def main():
    generate_wall()
    
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
        
        # First clear the screen and then draw wall
        screen.fill(BACKGROUND_COLOR)
        draw_wall()
        
        # Display current bond type and controls
        if current_bond_type == BondType.NORMAL:
            bond_name = "NORMAL"
        elif current_bond_type == BondType.FLEMISH:
            bond_name = "FLEMISH"
        else:
            bond_name = "WILD"
        bond_type_string = f"Current Bond: {bond_name}"
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
