from panda3d.core import loadPrcFile, loadPrcFileData
loadPrcFile("etc/Config.prc")

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from perlin_noise import PerlinNoise
import random
import math
import time

# Initialize Perlin noise
noise = PerlinNoise(octaves=3, seed=random.randint(1, 1000))

# Initialize the Ursina app
app = Ursina()

window.fps_counter.enabled = False  # Hide the FPS counter
application.development_mode = False  # Disable developer mode

# Game settings
selected_block = "grass"
spawn_point = Vec3(0, 5, 0)

# Create the player
player = FirstPersonController(
    mouse_sensitivity=Vec2(100, 100),
    position=spawn_point
)
player.flying = False  # Track flying state
last_space_press_time = 0  # For detecting double-space

# Load block textures
block_textures = {
    "grass": load_texture("assets/textures/groundEarth.png"),
    "dirt": load_texture("assets/textures/groundMud.png"),
    "stone": load_texture("assets/textures/wallStone.png"),
    "bedrock": load_texture("assets/textures/stone07.png")
}

# Block class
class Block(Entity):
    def __init__(self, position, block_type):
        super().__init__(
            position=position,
            model="assets/models/block_model",
            scale=1,
            origin_y=-0.5,
            texture=block_textures.get(block_type),
            collider="box",
            visible=False  # Default to invisible for optimization
        )
        self.block_type = block_type

# Mini block for UI
mini_block = Entity(
    parent=camera,
    model="assets/models/block_model",
    scale=0.2,
    texture=block_textures.get(selected_block),
    position=(0.35, -0.25, 0.5),
    rotation=(-15, -30, -5)
)

# Create the ground
ground_blocks = []
min_height = -5
for x in range(-10, 10):
    for z in range(-10, 10):
        height = noise([x * 0.02, z * 0.02])
        height = math.floor(height * 7.5)
        for y in range(height, min_height - 1, -1):
            block_type = (
                "bedrock" if y == min_height
                else "grass" if y == height
                else "stone" if height - y > 2
                else "dirt"
            )
            block = Block((x, y + min_height, z), block_type)
            ground_blocks.append(block)

# Add sky
sky = Entity(
    model='sphere',
    texture=load_texture('assets/textures/sky_blue.jpg'),
    scale=500,
    double_sided=True
)

def main():
    pass


# Toggle fly mode
def toggle_fly_mode():
    player.flying = not player.flying
    if player.flying:
        player.gravity = 0  # Disable gravity
        player.velocity = Vec3(0, 0, 0)  # Stop movement
    else:
        player.gravity = 1  # Enable gravity

# Input handling
def input(key):
    global selected_block, last_space_press_time

    if key == "left mouse down":
        hit_info = raycast(camera.world_position, camera.forward, distance=10)
        if hit_info.hit:
            block = Block(hit_info.entity.position + hit_info.normal, selected_block)
            block.visible = True
            ground_blocks.append(block)
    if key == "right mouse down" and mouse.hovered_entity:
        if mouse.hovered_entity.block_type != "bedrock":
            ground_blocks.remove(mouse.hovered_entity)  # Remove from the list
            destroy(mouse.hovered_entity)

    # Block selection
    if key in "123":
        selected_block = list(block_textures.keys())[int(key) - 1]

    # Double-space to toggle fly mode
    if key == "space":
        current_time = time.time()
        if current_time - last_space_press_time < 0.3:  # Detect double-press
            toggle_fly_mode()
        last_space_press_time = current_time

# Update loop
def update():
    global ground_blocks
    for block in ground_blocks[:]:  # Iterate over a copy of the list
        if not block.enabled:  # Skip invalid blocks
            ground_blocks.remove(block)
            continue
        try:
            block.visible = distance(block.position, player.position) < 10
        except AssertionError:
            ground_blocks.remove(block)  # Clean up invalid blocks
    
    mini_block.texture = block_textures.get(selected_block)
    
    # Handle flying movement
    if player.flying:
        player.y += held_keys["space"] * 5 * time.dt
        player.y -= held_keys["shift"] * 5 * time.dt  # Go down with Shift

    # Reset player if they fall
    if player.position.y < -10:
        player.position = spawn_point
        player.velocity = Vec3(0, 0, 0)

# Run the app
app.run()

if __name__ == '__main__':
    main()