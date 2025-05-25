init python:
    import time
    import random # For particle effects

    # --- Global State Flags ---
    wrong_input_active = False
    wrong_input_start_time = None
    penalty_active = False
    is_cutscene_active = False
    puzzle_stage = 0 # Initialize puzzle_stage
    # --- End Global State Flags ---

    # --- Jaily State ---
    class JailyState:
        def __init__(self):
            self.trust = 75
            self.excitement = 50
            self.temperature = 98.6
            self.embarrassment = 10
            self.game_over = False

    jaily = JailyState() # Initial instance

    # --- Configuration Dictionaries ---
    adjustable_config = {
        "required_hold_time": 1.0,
        "cooldown_duration": 0.5,
        "particle_transition_duration": 3.0, # Time for PPS to reach target
        "pps_at_lower_bound": 0.2, # Base PPS when excitement is low
        "wrong_grace_period": 2.0, # Time before penalty for wrong input
        "wrong_transition_duration": 1.0, # Time for penalty to fully apply
        "temp_lower_game_over": 95.0, # Temperature threshold for game over
        "temp_upper_game_over": 103.0, # Temperature threshold for game over (already used in puzzle_state_check)
        "heart_shower": {"duration": 0.5, "count": 5}, # Config for heart shower
        "particle_update_interval": 0.05, # How often particle system updates
        "button_xysize": (150, 75), # Default size for puzzle buttons
        "max_particles_on_screen": 200, # Limit total particles
    }

    particle_config = { # For generic particles (e.g. touch)
        "fadeout_start": 0.5, # Time in seconds before fadeout begins
        "lifetime": 1.0,      # Total lifetime of a particle
        "image": "heart.png"  # Default particle image (ensure this exists or use a character)
    }
    particle_config_excitement = {
        "particles_per_sec": 10, # Base particles per second, will be modulated by excitement
        "fadeout_start": 1.0,
        "lifetime": 2.0,
        "image": "sparkle.png" # Image for excitement (ensure this exists or use a character)
    }
    particle_config_trust = {
        "particles_per_sec": 5, # Base particles per second for trust events
        "fadeout_start": 1.0,
        "lifetime": 2.5,
        "image": "glow.png" # Image for trust (ensure this exists or use a character)
    }

    # --- Particle Lists ---
    # Each particle could be a dict: {'x':0, 'y':0, 'spawn_time':0, 'image':'heart.png', 'zoom':1, 'rotate':0, 'type':'generic'}
    particles = []
    excitement_particles = []
    trust_particles = []
    heart_shower_anim = [] # List of dicts for active heart shower animations

    # --- Stubbed Functions ---
    def get_hotzone_multiplier():
        """Returns a multiplier for hold times, potentially based on game state."""
        return 1.0

    def spawn_particle(pos, p_type="generic"):
        """Spawns a particle at a given position."""
        global particles, excitement_particles, trust_particles, adjustable_config
        now = time.time()
        
        # Limit total particles to prevent performance issues
        if len(particles) + len(excitement_particles) + len(trust_particles) > adjustable_config.get("max_particles_on_screen", 200):
            return

        particle_data = {
            'x': pos[0],
            'y': pos[1],
            'spawn_time': now,
            'zoom': random.uniform(0.5, 1.2),
            'rotate': random.uniform(0, 360),
        }

        if p_type == "excitement":
            particle_data.update({
                'image': particle_config_excitement["image"],
                'config': particle_config_excitement,
                'list_ref': excitement_particles
            })
            excitement_particles.append(particle_data)
        elif p_type == "trust":
            particle_data.update({
                'image': particle_config_trust["image"],
                'config': particle_config_trust,
                'list_ref': trust_particles
            })
            trust_particles.append(particle_data)
        else: # Generic
            particle_data.update({
                'image': particle_config["image"],
                'config': particle_config,
                'list_ref': particles
            })
            particles.append(particle_data)


    def init_heart_shower_anim():
        """Initializes data for the heart shower animation screen."""
        global heart_shower_anim, adjustable_config
        heart_shower_anim = [] # Clear previous
        count = adjustable_config["heart_shower"].get("count", 5)
        for _ in range(count):
            heart_shower_anim.append({
                "heart_img": particle_config["image"], # Use generic heart image
                "x_start": random.randint(50, config.screen_width - 50),
                "y_start": random.randint(50, config.screen_height - 50),
                "x_end": random.randint(50, config.screen_width - 50),
                "y_end": random.randint(50, config.screen_height - 50),
                "r_rotate": random.uniform(0, 360),
                "r_scale": random.uniform(0.5, 1.5)
            })

    def compute_pps(excitement_level):
        """Computes particles per second based on excitement level."""
        # Example: PPS increases with excitement
        base_pps = particle_config_excitement["particles_per_sec"]
        return int(base_pps * (excitement_level / 100.0) * 2) # Max 2x base at 100 excitement

    _last_stat_update_time = time.time()
    def update_stats(interacting):
        """Placeholder for updating Jaily's stats based on interaction."""
        global _last_stat_update_time, jaily # Added jaily
        now = time.time()
        delta = now - _last_stat_update_time
        _last_stat_update_time = now

        if interacting:
            jaily.excitement = min(100, jaily.excitement + delta * 0.5) # Slow increase
            jaily.temperature += delta * 0.05
        else:
            jaily.excitement = max(0, jaily.excitement - delta * 0.2) # Slow decrease
            jaily.temperature -= delta * 0.02
        
        jaily.temperature = round(jaily.temperature, 2)


    update_stats.last_time = time.time() # For Puzzle.reset compatibility

    def is_interacting():
        """Placeholder to check if the player is currently interacting with sensitive zones."""
        return persistent.game_mouse_pressed and current_puzzle is not None


    def _cleanup_particle_list(particle_list, now):
        """Helper to remove old particles from a specific list."""
        idx = 0
        while idx < len(particle_list):
            p = particle_list[idx]
            # Use the specific config for this particle type for lifetime
            cfg = p.get('config', particle_config) # Default to generic if somehow missing
            if (now - p['spawn_time']) > cfg["lifetime"]:
                particle_list.pop(idx)
            else:
                idx += 1
                
    def cleanup_particles():
        """Removes particles that have exceeded their lifetime."""
        global particles, excitement_particles, trust_particles
        now = time.time()
        _cleanup_particle_list(particles, now)
        _cleanup_particle_list(excitement_particles, now)
        _cleanup_particle_list(trust_particles, now)


    def update_particle_system():
        """Periodically called to spawn new particles based on game state (e.g., excitement)."""
        global jaily, particle_config_excitement, current_puzzle
        if current_puzzle and is_interacting(): # Only spawn if puzzle active and interacting
            # Example: Spawn excitement particles based on current excitement
            # This is different from the PPS calculation in Puzzle.rub_timer which directly sets particle_config_excitement["particles_per_sec"]
            # This function could be for ambient particles or effects not tied to rub_timer's direct PPS control.
            # For now, let's keep it simple and not double-dip on excitement PPS generation if rub_timer handles it.
            # One option: rub_timer controls the *potential* PPS, this function actually *spawns* them over time.
            # However, rub_timer already updates particle_config_excitement["particles_per_sec"].
            # Let's assume this is for other types of particles or general particle management.
            pass # For now, let rub_timer handle the excitement particle rate.
                 # This function could be used for other ambient effects later.

    # --- End Stubbed Functions ---

    # --- Puzzle Logic (shared parts) ---
    # Base Puzzle class, moved from puzzle1.rpy
    class Puzzle:
        def __init__(self):
            # Default sequence for Puzzle 1, others will override in their __init__
            self.sequence = []
            self.current_seq_index = 0
            self.hold_start_time = {} 
            self.current_active_zone = None
            self.cooldown_end = 0.0
            self.last_particle_update = time.time()
            self.initial_touch_spawned = False
            self.initial_touch_spawned_cooldown = False
            self.played_cutscene = False
            self.puzzle_type_id = 1 # Default to 1, subclasses like Puzzle2 will change this
            self.reset()

        def process_zone(self, zone, now, expected_zone):
            """Checks if the correct zone is being held long enough."""
            # global adjustable_config, get_hotzone_multiplier # These are read from global scope
            current_hold_start = self.hold_start_time.get(zone)
            if self.current_active_zone == zone and zone == expected_zone:
                if current_hold_start is None:
                    self.hold_start_time[zone] = now
                elif now - current_hold_start >= adjustable_config["required_hold_time"] / get_hotzone_multiplier():
                    self.hold_start_time[zone] = None
                    return True
            else:
                if zone in self.hold_start_time:
                    self.hold_start_time[zone] = None
            return False

        def check_and_trigger_cutscenes(self):
            """Checks if the current puzzle state should trigger a cutscene."""
            global is_cutscene_active 
            # This method will be generic. Puzzle-specific cutscenes can be handled
            # by overriding this method in subclasses (like Puzzle2 already does),
            # or by adding more conditions based on self.puzzle_type_id.
            if self.puzzle_type_id == 1: 
                if self.current_seq_index == 6 and not self.played_cutscene:
                    is_cutscene_active = True
                    self.played_cutscene = True
                    renpy.call("cut_scene1_label") # Specific to Puzzle 1
                    is_cutscene_active = False
                    if self.current_seq_index < len(self.sequence):
                        # Ensure the zone key exists before trying to access it
                        if self.sequence[self.current_seq_index] in self.hold_start_time:
                           self.hold_start_time[self.sequence[self.current_seq_index]] = None
            # Note: Puzzle2 has its own check_and_trigger_cutscenes method, which will be called for Puzzle2 instances.
            # If other puzzles (3,4,5) need specific cutscenes, they should also override this method.


        def rub_timer(self):
            """Processes player interaction, sets flags like wrong_input_active."""
            global wrong_input_active, wrong_input_start_time, penalty_active, is_cutscene_active, jaily, particle_config_excitement, adjustable_config
            # Screen variables (clicked_zone1, etc., clicked_cooldown) are accessed from the store via default.
            # Ren'Py functions like renpy.get_mouse_pos(), renpy.get_mouse_pressed() are used directly.
            # Global functions like spawn_particle, init_heart_shower_anim, get_hotzone_multiplier, compute_pps are called.
            
            if is_cutscene_active: return
            now = time.time()
            if now < self.cooldown_end:
                self.current_active_zone = None
                wrong_input_active = False
                wrong_input_start_time = None
                penalty_active = False
                for zone in self.hold_start_time: self.hold_start_time[zone] = None
                return
            
            if clicked_cooldown and persistent.game_mouse_pressed: 
                self.current_active_zone = None
                wrong_input_active = False
                wrong_input_start_time = None
                penalty_active = False
                for zone in self.hold_start_time: self.hold_start_time[zone] = None
                if not self.initial_touch_spawned_cooldown:
                   spawn_particle(renpy.get_mouse_pos())
                   self.initial_touch_spawned_cooldown = True
                return
            else: self.initial_touch_spawned_cooldown = False

            expected_zone = self.sequence[self.current_seq_index] if self.current_seq_index < len(self.sequence) else None
            var_previous_zone = self.current_active_zone
            new_active_zone = None
            mouse_is_down = persistent.game_mouse_pressed

            if mouse_is_down:
                if clicked_zone1: new_active_zone = "zone1"
                elif clicked_zone2: new_active_zone = "zone2"
                elif clicked_zone3: new_active_zone = "zone3"
                elif clicked_zone4: new_active_zone = "zone4"
                elif clicked_zone5: new_active_zone = "zone5"
                elif clicked_zone6: new_active_zone = "zone6"
                elif clicked_zone7: new_active_zone = "zone7"
                elif clicked_zone8: new_active_zone = "zone8"
                elif clicked_locked1: new_active_zone = "locked1"
                elif clicked_locked2: new_active_zone = "locked2"
                elif clicked_locked3: new_active_zone = "locked3"
                elif clicked_locked4: new_active_zone = "locked4"
                elif clicked_locked5: new_active_zone = "locked5"
                elif clicked_locked6: new_active_zone = "locked6"
                elif clicked_locked7: new_active_zone = "locked7"
                elif clicked_locked8: new_active_zone = "locked8"
                elif clicked_locked9: new_active_zone = "locked9"
                elif clicked_locked10: new_active_zone = "locked10"
                elif clicked_locked11: new_active_zone = "locked11"
                elif clicked_locked12: new_active_zone = "locked12"
                elif clicked_locked13: new_active_zone = "locked13"
                elif clicked_locked14: new_active_zone = "locked14"
            
            changed_zone = (new_active_zone != var_previous_zone)
            self.current_active_zone = new_active_zone

            if not mouse_is_down:
                for zone_key in self.hold_start_time: self.hold_start_time[zone_key] = None
                wrong_input_active = False
                wrong_input_start_time = None
                penalty_active = False
            elif changed_zone and var_previous_zone is not None and var_previous_zone in self.hold_start_time:
                self.hold_start_time[var_previous_zone] = None

            if self.current_active_zone and mouse_is_down:
                if self.current_active_zone not in self.hold_start_time:
                     self.hold_start_time[self.current_active_zone] = None
                if self.current_active_zone == expected_zone:
                    wrong_input_active = False
                    wrong_input_start_time = None
                    penalty_active = False
                    if self.process_zone(self.current_active_zone, now, expected_zone):
                        self.current_seq_index += 1
                        self.cooldown_end = now + adjustable_config["cooldown_duration"] / get_hotzone_multiplier()
                        init_heart_shower_anim() 
                        renpy.show_screen("FlashScreen") 
                        wrong_input_active = False
                        wrong_input_start_time = None
                        penalty_active = False
                        self.check_and_trigger_cutscenes() 
                else: 
                    if not wrong_input_active:
                        wrong_input_start_time = now
                        wrong_input_active = True
                    if expected_zone and expected_zone in self.hold_start_time:
                        self.hold_start_time[expected_zone] = None
            
            dt_particles = now - self.last_particle_update
            if dt_particles > 0:
                target_particles = compute_pps(jaily.excitement)
                current_particles_val = particle_config_excitement["particles_per_sec"] # Renamed to avoid conflict
                transition_duration = max(0.001, adjustable_config.get("particle_transition_duration", 5.0))
                base_rate = adjustable_config.get("pps_at_lower_bound", 0.2)
                transition_rate = base_rate / transition_duration
                if current_particles_val < target_particles:
                    current_particles_val = min(target_particles, current_particles_val + transition_rate * dt_particles)
                elif current_particles_val > target_particles:
                    current_particles_val = max(target_particles, current_particles_val - transition_rate * dt_particles)
                particle_config_excitement["particles_per_sec"] = current_particles_val
                self.last_particle_update = now

            if changed_zone:
                if self.current_active_zone is not None and not self.initial_touch_spawned:
                    spawn_particle(renpy.get_mouse_pos()) 
                    self.initial_touch_spawned = True
                if self.current_active_zone is None:
                    self.initial_touch_spawned = False

        def update(self):
            """Called periodically. Handles grace period timing AND calls external stat update."""
            global wrong_input_active, wrong_input_start_time, penalty_active, is_cutscene_active, adjustable_config
            # update_stats and is_interacting are global scope functions
            self.rub_timer()
            if not is_cutscene_active:
                if wrong_input_active and wrong_input_start_time is not None and not penalty_active:
                    now = time.time()
                    wrong_elapsed = now - wrong_input_start_time
                    grace = adjustable_config.get("wrong_grace_period", 5.0)
                    transition = adjustable_config.get("wrong_transition_duration", 1.0)
                    if wrong_elapsed >= grace + transition:
                        penalty_active = True
                update_stats(is_interacting())

        def reset(self):
            """Resets the puzzle state."""
            global wrong_input_active, wrong_input_start_time, penalty_active 
            # particles, excitement_particles, trust_particles are global lists modified directly
            global particles, excitement_particles, trust_particles 
            # update_stats is a global function/object with a 'last_time' attribute
            # global update_stats 

            self.current_seq_index = 0
            self.played_cutscene = False

            # Ensure self.sequence is set by __init__ of the specific puzzle instance (Puzzle1, Puzzle2, etc.)
            all_possible_zones = set(self.sequence) 
            all_possible_zones.update([
                "zone1", "zone2", "zone3", "zone4", "zone5", "zone6", "zone7", "zone8",
                "locked1", "locked2", "locked3", "locked4", "locked5", "locked6",
                "locked7", "locked8", "locked9", "locked10", "locked11",
                "locked12", "locked13", "locked14"
            ])
            self.hold_start_time = {zone: None for zone in all_possible_zones}

            self.current_active_zone = None
            self.cooldown_end = 0.0
            self.last_particle_update = time.time()
            self.initial_touch_spawned = False
            self.initial_touch_spawned_cooldown = False

            wrong_input_active = False
            wrong_input_start_time = None
            penalty_active = False

            if hasattr(update_stats, 'last_time'): 
                update_stats.last_time = time.time()

            particles[:] = []
            excitement_particles[:] = []
            trust_particles[:] = []

    class Puzzle2(Puzzle):
        def __init__(self):
            super(Puzzle2, self).__init__()
            self.sequence = ["zone2", "zone2", "zone1", "zone1", "locked1", "zone1", "zone2", "locked1", "locked1", "locked2", "zone1", "zone2", "locked2"]
            self.puzzle_type_id = 2

        def check_and_trigger_cutscenes(self):
            global is_cutscene_active
            if self.current_seq_index == 5 and not self.played_cutscene:
                is_cutscene_active = True
                self.played_cutscene = True
                renpy.call("cut_scene2_label")
                is_cutscene_active = False
                if self.current_seq_index < len(self.sequence): # Check needed for safety
                    # Ensure the zone key exists before trying to access it
                    if self.sequence[self.current_seq_index] in self.hold_start_time:
                        self.hold_start_time[self.sequence[self.current_seq_index]] = None


    class Puzzle3(Puzzle):
        def __init__(self):
            super(Puzzle3, self).__init__()
            self.sequence = ["zone3", "zone3", "zone4", "zone3", "locked3", "zone4", "locked3", "zone4", "zone3", "locked4", "zone4", "locked3", "zone3", "locked4", "locked5", "zone4", "zone3", "locked5", "locked5"]
            self.puzzle_type_id = 3

    class Puzzle4(Puzzle):
        def __init__(self):
            super(Puzzle4, self).__init__()
            self.sequence = ["zone5", "zone6", "zone6", "zone5", "locked6", "zone6", "zone5", "locked6", "locked7", "zone5", "locked7", "locked7", "zone6", "locked8", "locked6", "locked8", "locked7", "locked8", "locked9", "locked9", "locked7", "locked8", "locked9"]
            self.puzzle_type_id = 4

    class Puzzle5(Puzzle):
        def __init__(self):
            super(Puzzle5, self).__init__()
            self.sequence = ["zone7", "zone8", "zone7", "locked10", "zone8", "zone7", "locked10", "locked11", "zone8", "locked11", "locked10", "locked12", "zone8", "locked11", "zone8", "locked13", "zone7", "locked10", "locked12", "locked13", "locked14", "locked11", "locked10", "locked12", "locked13", "locked14", "locked10", "locked14"]
            self.puzzle_type_id = 5

    current_puzzle = None

    def reset_game():
        global jaily, current_puzzle
        jaily = JailyState() # Reset Jaily's state
        if current_puzzle:
             current_puzzle.reset()

    def puzzle_state_check():
        global is_cutscene_active, current_puzzle, jaily, adjustable_config # Added adjustable_config
        if current_puzzle:
            current_puzzle.update()
        if not is_cutscene_active:
            if jaily.game_over:
                # Order of checks matters if multiple conditions can be true
                if jaily.temperature >= adjustable_config.get("temp_upper_game_over", 103.0): renpy.jump("game_over_max_temp")
                elif jaily.embarrassment >= 100: renpy.jump("game_over_embarrassment")
                elif jaily.trust <= 0: renpy.jump("game_over_trust")
                elif jaily.excitement <= 0: renpy.jump("game_over_excitement")
                elif jaily.temperature <= adjustable_config.get("temp_lower_game_over", 95.0): renpy.jump("game_over_low_temp")
            elif current_puzzle and current_puzzle.current_seq_index >= len(current_puzzle.sequence):
                renpy.jump("outcome_puzzle")

# --- Default Clicked Zone Flags ---
default persistent.game_mouse_pressed = False
default clicked_zone1 = False
default clicked_zone2 = False
default clicked_zone3 = False
default clicked_zone4 = False
default clicked_zone5 = False
default clicked_zone6 = False
default clicked_zone7 = False
default clicked_zone8 = False
default clicked_locked1 = False
default clicked_locked2 = False
default clicked_locked3 = False
default clicked_locked4 = False
default clicked_locked5 = False
default clicked_locked6 = False
default clicked_locked7 = False
default clicked_locked8 = False
default clicked_locked9 = False
default clicked_locked10 = False
default clicked_locked11 = False
default clicked_locked12 = False
default clicked_locked13 = False
default clicked_locked14 = False
default clicked_cooldown = False

# --- SCREENS ---
# (Assuming heart.png, sparkle.png, glow.png exist or are characters like u"❤")
# If using actual image files, ensure they are in the game/images/ directory or similar
# For simplicity, one could replace `add p['image']` with `text "debug"` or a fixed character.

transform heart_shower(x_start, y_start, x_end, y_end, rotate, scale):
    pos (x_start, y_start)
    rotate rotate
    zoom scale
    alpha 1.0
    linear adjustable_config["heart_shower"]["duration"]: # ensure this key exists
         pos (x_end, y_end)
         alpha 0.0

screen FlashScreen():
    modal False
    zorder 5000
    timer adjustable_config["heart_shower"]["duration"] action Hide("FlashScreen")
    for data in heart_shower_anim:
        add data["heart_img"] at heart_shower(data["x_start"], data["y_start"], data["x_end"], data["y_end"], data["r_rotate"], data["r_scale"])

screen particles_screen():
    zorder 2000
    # Optimized: timer calls cleanup_particles once, cleanup_particles handles all lists
    timer 0.1 action Function(cleanup_particles) repeat True

    # Generic particles
    for p in particles:
        $ age = time.time() - p['spawn_time']
        $ cfg = p.get('config', particle_config)
        $ current_alpha = 1.0 if age < cfg["fadeout_start"] else max(0.0, ((cfg["lifetime"] - age) / max(0.001, (cfg["lifetime"] - cfg["fadeout_start"]))))
        add p['image'] at Transform(anchor=(0.5, 0.5), pos=(p['x'], p['y']), zoom=p['zoom'], rotate=p['rotate'], alpha=current_alpha)

    # Excitement particles
    for p in excitement_particles:
        $ age = time.time() - p['spawn_time']
        $ cfg = p.get('config', particle_config_excitement)
        $ current_alpha = 1.0 if age < cfg["fadeout_start"] else max(0.0, ((cfg["lifetime"] - age) / max(0.001, (cfg["lifetime"] - cfg["fadeout_start"]))))
        add p['image'] at Transform(anchor=(0.5, 0.5), pos=(p['x'], p['y']), zoom=p['zoom'], rotate=p['rotate'], alpha=current_alpha)

    # Trust particles
    for p in trust_particles:
        $ age = time.time() - p['spawn_time']
        $ cfg = p.get('config', particle_config_trust)
        $ current_alpha = 1.0 if age < cfg["fadeout_start"] else max(0.0, ((cfg["lifetime"] - age) / max(0.001, (cfg["lifetime"] - cfg["fadeout_start"]))))
        add p['image'] at Transform(anchor=(0.5, 0.5), pos=(p['x'], p['y']), zoom=p['zoom'], rotate=p['rotate'], alpha=current_alpha)


screen ParticleManagerScreen():
    zorder 1000
    # update_particle_system is currently a pass, so this screen doesn't do much yet.
    timer adjustable_config["particle_update_interval"] action Function(update_particle_system) repeat True

screen puzzle_stats_update(): # Renamed from Primary_stats_update to match call in puzzle1
    timer 0.1 action Function(lambda: update_stats(is_interacting()) if not is_cutscene_active else None) repeat True

screen game_state_check():
    timer 0.1 action Function(puzzle_state_check) repeat True

screen Primary_stats(): # Screen to display Jaily's stats
    frame:
        xalign 0.0 # Changed to 0.0 for top-left
        yalign 0.0 # Changed to 0.0 for top-left
        padding (10, 10)
        background None # Transparent background
        style "empty" # Use if you have a style named "empty", else remove
        vbox:
            spacing 8
            text "Trust: [int(jaily.trust)]" size 18
            bar value jaily.trust range 100 xmaximum 150
            text "Excitement: [round(jaily.excitement)]" size 18
            bar value jaily.excitement range 100 xmaximum 150
            text "Temperature: [jaily.temperature:.2f]" size 18
            bar value jaily.temperature range adjustable_config.get("temp_upper_game_over", 103.0) xmaximum 150 # Use config for range
            text "Embarrassment: [int(jaily.embarrassment)]" size 18
            bar value jaily.embarrassment range 100 xmaximum 150

screen sequence_display():
    frame:
        xalign 0.5
        yalign 0.05 # Slightly lower
        background "#00000080" # Semi-transparent black
        padding (10,10)
        if current_puzzle and hasattr(current_puzzle, 'sequence'):
            text "[', '.join(current_puzzle.sequence)]" size 20 color "#FFFFFF" # Smaller text
        else:
            text "No puzzle active" size 20 color "#FFFFFF"

screen GameplayScreen():
    zorder 100
    modal True # Blocks interaction with things behind it
    $ puzzle_id = current_puzzle.puzzle_type_id if current_puzzle and hasattr(current_puzzle, 'puzzle_type_id') else 0

    vbox:
        xalign 0.5
        yalign 0.5
        spacing 20

        button: # Cooldown button always visible
            style "cyan_cooldown" # Make sure this style is defined
            action NullAction()
            hovered [SetVariable("clicked_cooldown", True), SetVariable("persistent.game_mouse_pressed", True)]
            unhovered [SetVariable("clicked_cooldown", False), SetVariable("persistent.game_mouse_pressed", False)]
            text "Cooldown" xalign 0.5 yalign 0.5

        # Conditional HBox for puzzle zones based on puzzle_id
        if puzzle_id == 1:
            hbox:
                spacing 20
                button:
                    style "red_hotzone"
                    action NullAction()
                    hovered [SetVariable("clicked_zone1", True), SetVariable("persistent.game_mouse_pressed", True)]
                    unhovered [SetVariable("clicked_zone1", False), SetVariable("persistent.game_mouse_pressed", False)]
                    text "Zone1"
                    xalign 0.5
                    yalign 0.5
                button:
                    style "green_hotzone"
                    action NullAction()
                    hovered [SetVariable("clicked_zone2", True), SetVariable("persistent.game_mouse_pressed", True)]
                    unhovered [SetVariable("clicked_zone2", False), SetVariable("persistent.game_mouse_pressed", False)]
                    text "Zone2"
                    xalign 0.5
                    yalign 0.5
                button:
                    style "blue_hotzone"
                    action NullAction()
                    hovered [SetVariable("clicked_locked1", True), SetVariable("persistent.game_mouse_pressed", True)]
                    unhovered [SetVariable("clicked_locked1", False), SetVariable("persistent.game_mouse_pressed", False)]
                    text "Locked1"
                    xalign 0.5
                    yalign 0.5
        elif puzzle_id == 2:
            hbox:
                spacing 20
                button:
                    style "red_hotzone"
                    action NullAction()
                    hovered [SetVariable("clicked_zone1", True), SetVariable("persistent.game_mouse_pressed", True)]
                    unhovered [SetVariable("clicked_zone1", False), SetVariable("persistent.game_mouse_pressed", False)]
                    text "Zone1"
                    xalign 0.5
                    yalign 0.5
                button:
                    style "green_hotzone"
                    action NullAction()
                    hovered [SetVariable("clicked_zone2", True), SetVariable("persistent.game_mouse_pressed", True)]
                    unhovered [SetVariable("clicked_zone2", False), SetVariable("persistent.game_mouse_pressed", False)]
                    text "Zone2"
                    xalign 0.5
                    yalign 0.5
                button:
                    style "blue_hotzone"
                    action NullAction()
                    hovered [SetVariable("clicked_locked1", True), SetVariable("persistent.game_mouse_pressed", True)]
                    unhovered [SetVariable("clicked_locked1", False), SetVariable("persistent.game_mouse_pressed", False)]
                    text "Locked1"
                    xalign 0.5
                    yalign 0.5
                button:
                    style "blue_hotzone"
                    action NullAction()
                    hovered [SetVariable("clicked_locked2", True), SetVariable("persistent.game_mouse_pressed", True)]
                    unhovered [SetVariable("clicked_locked2", False), SetVariable("persistent.game_mouse_pressed", False)]
                    text "Locked2"
                    xalign 0.5
                    yalign 0.5
        elif puzzle_id == 3: # Similar structure for Puzzles 3, 4, 5
            hbox:
                spacing 20
                button:
                    style "red_hotzone"
                    action NullAction()
                    hovered [SetVariable("clicked_zone3", True), SetVariable("persistent.game_mouse_pressed", True)]
                    unhovered [SetVariable("clicked_zone3", False), SetVariable("persistent.game_mouse_pressed", False)]
                    text "Zone3"
                    xalign 0.5
                    yalign 0.5
                button:
                    style "green_hotzone"
                    action NullAction()
                    hovered [SetVariable("clicked_zone4", True), SetVariable("persistent.game_mouse_pressed", True)]
                    unhovered [SetVariable("clicked_zone4", False), SetVariable("persistent.game_mouse_pressed", False)]
                    text "Zone4"
                    xalign 0.5
                    yalign 0.5
                button:
                    style "blue_hotzone"
                    action NullAction()
                    hovered [SetVariable("clicked_locked3", True), SetVariable("persistent.game_mouse_pressed", True)]
                    unhovered [SetVariable("clicked_locked3", False), SetVariable("persistent.game_mouse_pressed", False)]
                    text "Locked3"
                    xalign 0.5
                    yalign 0.5
                button:
                    style "blue_hotzone"
                    action NullAction()
                    hovered [SetVariable("clicked_locked4", True), SetVariable("persistent.game_mouse_pressed", True)]
                    unhovered [SetVariable("clicked_locked4", False), SetVariable("persistent.game_mouse_pressed", False)]
                    text "Locked4"
                    xalign 0.5
                    yalign 0.5
                button:
                    style "blue_hotzone"
                    action NullAction()
                    hovered [SetVariable("clicked_locked5", True), SetVariable("persistent.game_mouse_pressed", True)]
                    unhovered [SetVariable("clicked_locked5", False), SetVariable("persistent.game_mouse_pressed", False)]
                    text "Locked5"
                    xalign 0.5
                    yalign 0.5
        elif puzzle_id == 4:
            hbox:
                spacing 20
                button:
                    style "red_hotzone"
                    action NullAction()
                    hovered [SetVariable("clicked_zone5", True), SetVariable("persistent.game_mouse_pressed", True)]
                    unhovered [SetVariable("clicked_zone5", False), SetVariable("persistent.game_mouse_pressed", False)]
                    text "Zone5"
                    xalign 0.5
                    yalign 0.5
                button:
                    style "green_hotzone"
                    action NullAction()
                    hovered [SetVariable("clicked_zone6", True), SetVariable("persistent.game_mouse_pressed", True)]
                    unhovered [SetVariable("clicked_zone6", False), SetVariable("persistent.game_mouse_pressed", False)]
                    text "Zone6"
                    xalign 0.5
                    yalign 0.5
                button:
                    style "blue_hotzone"
                    action NullAction()
                    hovered [SetVariable("clicked_locked6", True), SetVariable("persistent.game_mouse_pressed", True)]
                    unhovered [SetVariable("clicked_locked6", False), SetVariable("persistent.game_mouse_pressed", False)]
                    text "Locked6"
                    xalign 0.5
                    yalign 0.5
                button:
                    style "blue_hotzone"
                    action NullAction()
                    hovered [SetVariable("clicked_locked7", True), SetVariable("persistent.game_mouse_pressed", True)]
                    unhovered [SetVariable("clicked_locked7", False), SetVariable("persistent.game_mouse_pressed", False)]
                    text "Locked7"
                    xalign 0.5
                    yalign 0.5
                button:
                    style "blue_hotzone"
                    action NullAction()
                    hovered [SetVariable("clicked_locked8", True), SetVariable("persistent.game_mouse_pressed", True)]
                    unhovered [SetVariable("clicked_locked8", False), SetVariable("persistent.game_mouse_pressed", False)]
                    text "Locked8"
                    xalign 0.5
                    yalign 0.5
                button:
                    style "blue_hotzone"
                    action NullAction()
                    hovered [SetVariable("clicked_locked9", True), SetVariable("persistent.game_mouse_pressed", True)]
                    unhovered [SetVariable("clicked_locked9", False), SetVariable("persistent.game_mouse_pressed", False)]
                    text "Locked9"
                    xalign 0.5
                    yalign 0.5
        elif puzzle_id == 5:
            hbox:
                # The hbox itself does not need 'spacing_outer = 10'
                # The 'spacing_inner = 10' was for the grid.
                # We will inline the value for the grid's spacing.
                grid 2 4: 
                    spacing 10 # Value of spacing_inner directly applied
                    button:
                        style "red_hotzone"
                        action NullAction()
                        hovered [SetVariable("clicked_zone7", True), SetVariable("persistent.game_mouse_pressed", True)]
                        unhovered [SetVariable("clicked_zone7", False), SetVariable("persistent.game_mouse_pressed", False)]
                        text "Zone7"
                        xalign 0.5
                        yalign 0.5
                    button:
                        style "green_hotzone"
                        action NullAction()
                        hovered [SetVariable("clicked_zone8", True), SetVariable("persistent.game_mouse_pressed", True)]
                        unhovered [SetVariable("clicked_zone8", False), SetVariable("persistent.game_mouse_pressed", False)]
                        text "Zone8"
                        xalign 0.5
                        yalign 0.5
                    button:
                        style "blue_hotzone"
                        action NullAction()
                        hovered [SetVariable("clicked_locked10", True), SetVariable("persistent.game_mouse_pressed", True)]
                        unhovered [SetVariable("clicked_locked10", False), SetVariable("persistent.game_mouse_pressed", False)]
                        text "Locked10"
                        xalign 0.5
                        yalign 0.5
                    button:
                        style "blue_hotzone"
                        action NullAction()
                        hovered [SetVariable("clicked_locked11", True), SetVariable("persistent.game_mouse_pressed", True)]
                        unhovered [SetVariable("clicked_locked11", False), SetVariable("persistent.game_mouse_pressed", False)]
                        text "Locked11"
                        xalign 0.5
                        yalign 0.5
                    button:
                        style "blue_hotzone"
                        action NullAction()
                        hovered [SetVariable("clicked_locked12", True), SetVariable("persistent.game_mouse_pressed", True)]
                        unhovered [SetVariable("clicked_locked12", False), SetVariable("persistent.game_mouse_pressed", False)]
                        text "Locked12"
                        xalign 0.5
                        yalign 0.5
                    button:
                        style "blue_hotzone"
                        action NullAction()
                        hovered [SetVariable("clicked_locked13", True), SetVariable("persistent.game_mouse_pressed", True)]
                        unhovered [SetVariable("clicked_locked13", False), SetVariable("persistent.game_mouse_pressed", False)]
                        text "Locked13"
                        xalign 0.5
                        yalign 0.5
                    button:
                        style "blue_hotzone"
                        action NullAction()
                        hovered [SetVariable("clicked_locked14", True), SetVariable("persistent.game_mouse_pressed", True)]
                        unhovered [SetVariable("clicked_locked14", False), SetVariable("persistent.game_mouse_pressed", False)]
                        text "Locked14"
                        xalign 0.5
                        yalign 0.5
                    null # Empty cell if needed for grid alignment

screen overheat_overlay():
    zorder 4999 # Just below FlashScreen
    timer 0.1 action NullAction() repeat True
    $ temp = jaily.temperature
    $ overlay_alpha = 0.0
    if temp > 102.0: # Start fading in after 102
        # Alpha from 0.0 at 102.0 to 0.25 at 103.0 (or higher, capped by min)
        $ overlay_alpha = (min(temp, adjustable_config.get("temp_upper_game_over", 103.0)) - 102.0) * 0.25
    add Solid("#ff0000", xysize=(config.screen_width, config.screen_height)) alpha max(0, overlay_alpha) # Ensure alpha isn't negative


# --- STYLE DEFINITIONS ---
init 2 python: # Ensure this runs after adjustable_config is defined
    style.red_hotzone = Style(style.button)
    style.red_hotzone.background = "#ff9999" # Slightly darker red
    style.red_hotzone.hover_background = "#ffcccc"
    style.red_hotzone.xysize = adjustable_config["button_xysize"]

    style.green_hotzone = Style(style.button)
    style.green_hotzone.background = "#99ff99" # Slightly darker green
    style.green_hotzone.hover_background = "#ccffcc"
    style.green_hotzone.xysize = adjustable_config["button_xysize"]

    style.blue_hotzone = Style(style.button)
    style.blue_hotzone.background = "#9999ff" # Slightly darker blue
    style.blue_hotzone.hover_background = "#ccccff"
    style.blue_hotzone.xysize = adjustable_config["button_xysize"]

    style.cyan_cooldown = Style(style.button)
    style.cyan_cooldown.background = "#99ffff" # Slightly darker cyan
    style.cyan_cooldown.hover_background = "#ccffff"
    style.cyan_cooldown.xysize = adjustable_config["button_xysize"]

# --- Consolidated hide for UI elements ---
label hide_all_ui:
    $ screens_to_hide = ["GameplayScreen", "ParticleManagerScreen", "particles_screen", "puzzle_stats_update", "Primary_stats", "game_state_check", "sequence_display", "overheat_overlay"]
    python:
        for s_name in screens_to_hide:
            if renpy.has_screen(s_name):
                renpy.hide_screen(s_name)
    return

# --- LABELS (Game Flow) ---
label flash_screen:
    show screen FlashScreen
    # Pause duration is handled by the FlashScreen timer itself
    return

label game_over_max_temp:
    call hide_all_ui
    "Game Over: Temperature too high! ([jaily.temperature:.2f])"
    return

label game_over_embarrassment:
    call hide_all_ui
    "Game Over: Embarrassment reached 100!"
    return

label game_over_trust:
    call hide_all_ui
    "Game Over: Trust has dropped to 0!"
    return

label game_over_excitement:
    call hide_all_ui
    "Game Over: Excitement dropped to 0!"
    return

label game_over_low_temp:
    call hide_all_ui
    "Game Over: Temperature too low! ([jaily.temperature:.2f])"
    return

label outcome_puzzle:
    call hide_all_ui
    "Congratulations! Puzzle [puzzle_stage] completed successfully!" # Use puzzle_stage
    $ next_story_label = "story{}".format(puzzle_stage + 1)
    jump expression next_story_label # Use jump expression

# --- Cutscene Labels ---
label cut_scene2_label: # Already defined in puzzle1.rpy, this is for Puzzle 2
    $ renpy.hide_screen("GameplayScreen") # Ensure gameplay is hidden
    window show
    "Jaily says: "sample scene for puzzle 2""
    menu:
        "Good":
            pass
        "Mid":
            pass
        "Bad":
            pass
        "Trust unlock":
            pass
    $ renpy.show_screen("GameplayScreen") # Restore gameplay screen
    return

