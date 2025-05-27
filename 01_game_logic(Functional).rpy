# This file will contain the core game logic, state management,
# general puzzle mechanics, and associated UI screens.

python early:
    jaily = None

init python:
    from collections import namedtuple # For Zone
    import random 
    import time 
    import pygame # For left_mouse_down

    # Initial data structures and generic Puzzle class for CUTSCENE FIX
    Zone = namedtuple("Zone", "x y width height")

    touch_zones = {
        1: { "zone1": Zone(0, 0, 100, 100) },
        2: { "zone1": Zone(50, 50, 100, 100) },
        3: { "zone1": Zone(100, 100, 100, 100) },
        4: { "zone1": Zone(150, 150, 100, 100) },
        5: { "zone1": Zone(200, 200, 100, 100) },
    }

    thresholds = {
        1: { "zone1": 5 },
        2: { "zone1": 5 },
        3: { "zone1": 5 },
        4: { "zone1": 5 },
        5: { "zone1": 5 },
    }

    puzzle_times = {
        1: 30,
        2: 30,
        3: 30,
        4: 30,
        5: 30,
    }

    # CUTSCENE FIX: Generalized Puzzle class (data model)
    class PuzzleData(object): # Renamed to PuzzleData to avoid conflict with main Puzzle class
        def __init__(self, puzzle_number, zones, thresholds, max_time):
            self.number = puzzle_number
            self.zones = zones
            self.thresholds = thresholds
            self.max_time = max_time
            self.timer = 0
            self.state = {}
            for zid in zones:
                self.state[zid] = 0

        def update(self, dt):
            self.timer += dt
            if self.timer > self.max_time:
                return 'timeout'
            for zid, amount in self.state.items():
                if amount >= self.thresholds.get(zid, float('inf')):
                    return 'complete'
            return None

        def process_zone(self, zone_id, amount):
            if zone_id in self.state:
                self.state[zone_id] += amount

        def is_over(self):
            status = self.update(0)
            return status in ('timeout', 'complete')

    puzzles_data = {} # Renamed to puzzles_data
    for num in range(1,6):
        puzzles_data[num] = PuzzleData( # Uses renamed PuzzleData
            puzzle_number=num,
            zones=touch_zones[num],
            thresholds=thresholds[num],
            max_time=puzzle_times[num]
        )

    # Global Player State
    class JailyState:
        def __init__(self):
            self.trust = 50
            self.excitement = 50
            self.hearts = 50  # New stat for hearts particles (used by particle_system)
            self.temperature = 98.6
            self.embarrassment = 50
            self.game_over = False

    jaily = JailyState()

    # Adjustable Configuration (reconciled - only non-particle keys)
    adjustable_config = {
        "cooldown_duration": 1.0,             # Cooldown after correct step
        "required_hold_time": 10.0,           # Time required to hold a zone
        "wrong_grace_period": 5.0,
        "wrong_transition_duration": 1.0,     # Transition time for wrong input penalty
        "penalty_excitement_rate": 0.05,
        "penalty_trust_rate": 0.05,
        "penalty_embarrassment_rate": 0.05,

        # EXCITEMENT CONFIG
        "excitement_increase_rate": 0.02,
        "excitement_decay_rate": 0.01,
        "excitement_stat_baseline": 50,
        "excitement_multiplier_at_min": 0.5,
        "excitement_multiplier_at_max": 1.5,

        # TRUST CONFIG
        "trust_increase_rate": 0.0075,
        "trust_decay_rate": 0.005,
        "trust_stat_baseline": 50,
        "trust_multiplier_at_min": 0.25,
        "trust_multiplier_at_max": 2.0,
        # "trust_particle_phase_offset" has been moved to particle_system.rpy

        # Hearts Particle CONFIG (Moved to particle_system.rpy)
        # "hearts_threshold": 25, (and other related keys)

        # Trust Particle Ranges (Moved to particle_system.rpy)
        # "trust_threshold": 31, (and other related keys)

        # Excitement Particle Ranges (Moved to particle_system.rpy)
        # "excitement_threshold": 25, (and other related keys)

        # "particle_transition_duration": 5.0, (Moved to particle_system.rpy)
        # "particle_update_interval": 0.016, (Moved to particle_system.rpy)

        # Temperature Config
        "temp_embarrassment_multiplier": 4.0,
        "temp_incr_rate": 0.05,
        "temp_decay_rate": 0.0025,
        "cooldown_zone_temp_reduction_rate": 0.5,
        "cooldown_zone_excitement_increase_rate": -2.0,
        "chill_penalty_temp_cooldown_rate": 0.2,
        "chill_penalty_excitement_decay_rate": 5.0,
        "chill_penalty_trust_decay_rate": 5.0,
        "temp_lower_game_over": 97.5,

        # Heart shower adjustable attributes (Moved to particle_system.rpy)
        # "heart_shower": { ... }
    }

    # Input Flags
    clicked_zone1 = False
    clicked_zone2 = False
    clicked_locked1 = False
    clicked_cooldown = False
    clicked_locked2 = False
    clicked_zone3 = False
    clicked_zone4 = False
    clicked_locked3 = False
    clicked_locked4 = False
    clicked_locked5 = False
    clicked_zone5 = False
    clicked_zone6 = False
    clicked_locked6 = False
    clicked_locked7 = False
    clicked_locked8 = False
    clicked_locked9 = False
    clicked_zone7 = False
    clicked_zone8 = False
    clicked_locked10 = False
    clicked_locked11 = False
    clicked_locked12 = False
    clicked_locked13 = False
    clicked_locked14 = False
    wrong_input_active = False
    wrong_input_start_time = None
    penalty_active = False

    # Mouse and Interaction Helpers
    def left_mouse_down():
        return pygame.mouse.get_pressed()[0]

    def is_interacting():
        return ((clicked_zone1 or clicked_zone2 or clicked_zone3 or clicked_zone4 or
                 clicked_zone5 or clicked_zone6 or clicked_zone7 or clicked_zone8 or
                 clicked_locked1 or clicked_locked2 or clicked_locked3 or clicked_locked4 or
                 clicked_locked5 or clicked_locked6 or clicked_locked7 or clicked_locked8 or
                 clicked_locked9 or clicked_locked10 or clicked_locked11 or clicked_locked12 or
                 clicked_locked13 or clicked_locked14) and left_mouse_down())

    def get_hotzone_multiplier():
        baseline = adjustable_config["excitement_stat_baseline"]
        min_mult = adjustable_config["excitement_multiplier_at_min"]
        max_mult = adjustable_config["excitement_multiplier_at_max"]
        excitement = jaily.excitement
        if excitement <= baseline:
            return min_mult + (excitement / baseline) * (1.0 - min_mult)
        else:
            return 1.0 + ((excitement - baseline) / (100 - baseline)) * (max_mult - 1.0)

    def get_trust_penalty_multiplier():
        baseline = adjustable_config["trust_stat_baseline"]
        min_mult = adjustable_config["trust_multiplier_at_min"]
        max_mult = adjustable_config["trust_multiplier_at_max"]
        trust = jaily.trust
        if trust <= baseline:
            return max_mult + (trust / baseline) * (1.0 - max_mult)
        else:
            return 1.0 + ((trust - baseline) / (100 - baseline)) * (min_mult - 1.0)

    # Global Stats Update Function
    def update_stats(interacting):
        global penalty_active, wrong_input_active, wrong_input_start_time, jaily # Ensure jaily is treated as global
        current_time = time.time()
        # Ensure update_stats.last_time exists. It's initialized in the python block at the end of the file.
        dt = current_time - update_stats.last_time 
        update_stats.last_time = current_time

        dTemp = adjustable_config["temp_incr_rate"] * (1.0 if interacting else 0.0) - adjustable_config["temp_decay_rate"] * (jaily.temperature - 98.6)
        embarrassment_factor = (jaily.embarrassment / 100) * adjustable_config["temp_embarrassment_multiplier"]
        dTemp *= embarrassment_factor
        jaily.temperature += dTemp * dt

        if penalty_active:
            trust_multiplier = get_trust_penalty_multiplier()
            dExc = -adjustable_config["penalty_excitement_rate"] * jaily.excitement * trust_multiplier
            dTrust = -adjustable_config["penalty_trust_rate"] * jaily.trust * trust_multiplier
            dEmb = adjustable_config["penalty_embarrassment_rate"] * 100 * trust_multiplier
            jaily.excitement += dExc * dt
            jaily.trust += dTrust * dt
            jaily.embarrassment += dEmb * dt
        else:
            if wrong_input_active and wrong_input_start_time is not None:
                wrong_elapsed = current_time - wrong_input_start_time
                if wrong_elapsed < adjustable_config["wrong_grace_period"]:
                    factor = 1.0
                elif wrong_elapsed < adjustable_config["wrong_grace_period"] + (adjustable_config["wrong_transition_duration"] / get_hotzone_multiplier()):
                    factor = 1.0 - 2.0 * ((wrong_elapsed - adjustable_config["wrong_grace_period"]) / (adjustable_config["wrong_transition_duration"] / get_hotzone_multiplier()))
                else:
                    factor = -1.0
                I = factor
            else:
                I = 1.0 if interacting else 0.0

            fTemp = 1 + (jaily.temperature - 98.6) / (103.0 - 98.6) # Assumes 103.0 is max normal temp range
            dExc = adjustable_config["excitement_increase_rate"] * jaily.trust * I * fTemp - adjustable_config["excitement_decay_rate"] * jaily.excitement
            jaily.excitement += dExc * dt
            dTrust = adjustable_config["trust_increase_rate"] * jaily.excitement * I * fTemp - adjustable_config["trust_decay_rate"] * (jaily.trust - adjustable_config["trust_stat_baseline"])
            jaily.trust += dTrust * dt
            if jaily.trust > 100: jaily.trust = 100
        if jaily.excitement > 100: jaily.excitement = 100

        if clicked_cooldown and left_mouse_down():
            if jaily.temperature > 98.5: # Assuming 98.5 is a threshold
                jaily.temperature -= adjustable_config["cooldown_zone_temp_reduction_rate"] * dt
                jaily.excitement += adjustable_config["cooldown_zone_excitement_increase_rate"] * dt
            else:
                jaily.temperature -= adjustable_config["chill_penalty_temp_cooldown_rate"] * dt
                jaily.excitement -= adjustable_config["chill_penalty_excitement_decay_rate"] * dt
                jaily.trust -= adjustable_config["chill_penalty_trust_decay_rate"] * dt
        
        if (jaily.temperature >= 103.0 or jaily.embarrassment >= 100 or \
            jaily.trust <= 0 or jaily.excitement <= 0 or \
            jaily.temperature <= adjustable_config["temp_lower_game_over"]):
            jaily.game_over = True
    update_stats.last_time = time.time() # Initialized once when the script is first run

    # Main Puzzle Logic Class (gameplay version)
    class Puzzle: 
        def __init__(self):
            self.sequence = ["zone1", "zone2", "zone1", "zone2", "zone2", "locked1", "zone1", "locked1", "zone2", "locked1"]
            self.current_seq_index = 0
            self.hold_start_time = {
                "zone1": None, "zone2": None, "zone3": None, "zone4": None,
                "zone5": None, "zone6": None, "zone7": None, "zone8": None,
                "locked1": None, "locked2": None, "locked3": None, "locked4": None,
                "locked5": None, "locked6": None, "locked7": None, "locked8": None,
                "locked9": None, "locked10": None, "locked11": None, "locked12": None,
                "locked13": None, "locked14": None
            }
            self.ne1_unlocked = False 
            self.current_active_zone = None
            self.cooldown_end = 0.0
            self.last_particle_update = time.time() 
            self.initial_touch_spawned = False
            self.initial_touch_spawned_cooldown = False

        def process_zone(self, zone, now, expected_zone):
            if self.current_active_zone == zone and zone == expected_zone:
                if self.hold_start_time.get(zone) is None:
                    self.hold_start_time[zone] = now
                elif now - self.hold_start_time[zone] >= adjustable_config["required_hold_time"] / get_hotzone_multiplier():
                    self.hold_start_time[zone] = None
                    return True
            else: 
                if zone in self.hold_start_time: 
                    self.hold_start_time[zone] = None
            return False

        def rub_timer(self):
            global wrong_input_active, wrong_input_start_time, penalty_active, jaily
            global clicked_zone1, clicked_zone2, clicked_zone3, clicked_zone4, \
                   clicked_zone5, clicked_zone6, clicked_zone7, clicked_zone8, \
                   clicked_locked1, clicked_locked2, clicked_locked3, clicked_locked4, \
                   clicked_locked5, clicked_locked6, clicked_locked7, clicked_locked8, \
                   clicked_locked9, clicked_locked10, clicked_locked11, clicked_locked12, \
                   clicked_locked13, clicked_locked14, clicked_cooldown, left_mouse_down, \
                   adjustable_config_particles, particle_config_excitement, init_heart_shower_anim, spawn_particle, compute_pps
            
            now = time.time()
            if now < self.cooldown_end:
                self.current_active_zone = None; wrong_input_active = False; wrong_input_start_time = None; penalty_active = False
                for zone_key in self.hold_start_time: self.hold_start_time[zone_key] = None
                return

            if clicked_cooldown and left_mouse_down():
                self.current_active_zone = None; wrong_input_active = False; wrong_input_start_time = None; penalty_active = False
                return

            expected_zone = self.sequence[self.current_seq_index] if self.current_seq_index < len(self.sequence) else None
            
            previous_active_zone = self.current_active_zone
            new_active_zone = None
            if left_mouse_down():
                active_flags = {
                    "zone1": clicked_zone1, "zone2": clicked_zone2, "zone3": clicked_zone3, "zone4": clicked_zone4,
                    "zone5": clicked_zone5, "zone6": clicked_zone6, "zone7": clicked_zone7, "zone8": clicked_zone8,
                    "locked1": clicked_locked1, "locked2": clicked_locked2, "locked3": clicked_locked3, "locked4": clicked_locked4,
                    "locked5": clicked_locked5, "locked6": clicked_locked6, "locked7": clicked_locked7, "locked8": clicked_locked8,
                    "locked9": clicked_locked9, "locked10": clicked_locked10, "locked11": clicked_locked11, "locked12": clicked_locked12,
                    "locked13": clicked_locked13, "locked14": clicked_locked14
                }
                for zone_name, is_clicked in active_flags.items():
                    if is_clicked: new_active_zone = zone_name; break
            
            changed_zone = (new_active_zone != previous_active_zone)
            self.current_active_zone = new_active_zone

            for zone_key in list(self.hold_start_time.keys()):
                if zone_key != self.current_active_zone : 
                    self.hold_start_time[zone_key] = None
            
            if self.current_active_zone and self.process_zone(self.current_active_zone, now, expected_zone):
                self.current_seq_index += 1
                self.cooldown_end = now + adjustable_config["cooldown_duration"] / get_hotzone_multiplier()
                if 'init_heart_shower_anim' in globals() and callable(init_heart_shower_anim): init_heart_shower_anim() 
                renpy.show_screen("FlashScreen") 
                if self.current_active_zone in self.hold_start_time:
                     self.hold_start_time[self.current_active_zone] = None
                penalty_active = False 
            else: 
                if self.current_active_zone and left_mouse_down():
                    if self.current_active_zone != expected_zone:
                        if wrong_input_start_time is None: wrong_input_start_time = now
                        wrong_input_active = True
                        penalty_active = False 
                else: 
                    wrong_input_active = False
                    wrong_input_start_time = None
                    penalty_active = False

            dt_particles = now - self.last_particle_update
            if 'compute_pps' in globals() and callable(compute_pps) and \
               'particle_config_excitement' in globals() and 'adjustable_config_particles' in globals():
                target_exc_particles = compute_pps(jaily.excitement)
                current_exc_particles = particle_config_excitement["particles_per_sec"]
                # Ensure adjustable_config_particles has the needed keys with defaults
                pps_lower_bound = adjustable_config_particles.get("pps_at_lower_bound", 0.20)
                particle_transition_dur = adjustable_config_particles.get("particle_transition_duration", 5.0)
                if particle_transition_dur == 0: particle_transition_dur = 5.0 # Avoid division by zero
                
                transition_rate_exc = pps_lower_bound / particle_transition_dur

                if current_exc_particles < target_exc_particles:
                    current_exc_particles = min(target_exc_particles, current_exc_particles + transition_rate_exc * dt_particles)
                elif current_exc_particles > target_exc_particles:
                    current_exc_particles = max(target_exc_particles, current_exc_particles - transition_rate_exc * dt_particles)
                particle_config_excitement["particles_per_sec"] = current_exc_particles
            self.last_particle_update = now

            if changed_zone:
                if self.current_active_zone is not None and not self.initial_touch_spawned:
                    if 'spawn_particle' in globals() and callable(spawn_particle): spawn_particle(renpy.get_mouse_pos())
                    self.initial_touch_spawned = True
                if self.current_active_zone is None: self.initial_touch_spawned = False
            
            if clicked_cooldown and left_mouse_down():
                if not self.initial_touch_spawned_cooldown:
                    if 'spawn_particle' in globals() and callable(spawn_particle): spawn_particle(renpy.get_mouse_pos())
                    self.initial_touch_spawned_cooldown = True
            else: self.initial_touch_spawned_cooldown = False

        def update(self):
            self.rub_timer()
            update_stats(is_interacting()) 

        def reset(self):
            self.current_seq_index = 0
            self.hold_start_time = {k: None for k in self.hold_start_time}
            self.ne1_unlocked = False 
            self.current_active_zone = None
            global wrong_input_active, wrong_input_start_time, penalty_active, jaily, particles, excitement_particles, trust_particles
            wrong_input_active = False; wrong_input_start_time = None; penalty_active = False
            if 'update_stats' in globals() and hasattr(update_stats, 'last_time'): update_stats.last_time = time.time()
            self.cooldown_end = 0.0
            self.last_particle_update = time.time()
            self.initial_touch_spawned = False
            self.initial_touch_spawned_cooldown = False
            if 'particles' in globals(): particles[:] = []
            if 'excitement_particles' in globals(): excitement_particles[:] = []
            if 'trust_particles' in globals(): trust_particles[:] = []
            
    # Global Reset and Puzzle State Check Functions
    def reset_game():
        global jaily, current_puzzle 
        jaily = JailyState() 
        if current_puzzle and hasattr(current_puzzle, 'reset'):
            current_puzzle.reset()

    def puzzle_state_check():
        global jaily, current_puzzle, adjustable_config 
        if current_puzzle and hasattr(current_puzzle, 'update'):
            current_puzzle.update()
        
        if jaily.game_over:
            if jaily.temperature >= 103.0: renpy.jump("game_over_max_temp")
            elif jaily.embarrassment >= 100: renpy.jump("game_over_embarrassment")
            elif jaily.trust <= 0: renpy.jump("game_over_trust")
            elif jaily.excitement <= 0: renpy.jump("game_over_excitement")
            elif jaily.temperature <= adjustable_config["temp_lower_game_over"]: renpy.jump("game_over_low_temp")
        elif current_puzzle and hasattr(current_puzzle, 'sequence') and \
            current_puzzle.current_seq_index >= len(current_puzzle.sequence):
            renpy.jump("outcome_puzzle") 
    
    # Style Definitions
    style.red_hotzone = Style(style.button)
    style.red_hotzone.background = "#ffcccc"
    style.red_hotzone.hover_background = "#ffe6e6"
    style.red_hotzone.xysize = (150, 150)

    style.green_hotzone = Style(style.button)
    style.green_hotzone.background = "#ccffcc"
    style.green_hotzone.hover_background = "#e6ffe6"
    style.green_hotzone.xysize = (150, 150)

    style.blue_hotzone = Style(style.button)
    style.blue_hotzone.background = "#ccccff"
    style.blue_hotzone.hover_background = "#e6e6ff"
    style.blue_hotzone.xysize = (150, 150)

    style.cyan_cooldown = Style(style.button)
    style.cyan_cooldown.background = "#00ffff"
    style.cyan_cooldown.hover_background = "#e0ffff"
    style.cyan_cooldown.xysize = (150, 150)

# Screens (General Game UI)
screen TouchScreen(puzzle_number): 
    default current_puzzle_data = puzzles_data.get(puzzle_number) 
    if current_puzzle_data:
        default zones_to_display = current_puzzle_data.zones
        key "mouseup_1" action Function(puzzles_data[puzzle_number].process_zone, "some_zone_id_on_mouseup", 1) 
        for zone_id, zone_props in zones_to_display.items():
            imagemap:
                idle None 
                hover None 
                hotspot (zone_props.x, zone_props.y, zone_props.width, zone_props.height) action Function(puzzles_data[puzzle_number].process_zone, zone_id, 1) 

screen puzzle_stats_update():
    timer 0.1 action Function(lambda: update_stats(is_interacting())) repeat True

screen game_state_check():
    timer 0.1 action Function(puzzle_state_check) repeat True 

screen Primary_stats():
    if jaily is not None:
        frame:
            xalign 0.0
            yalign 0.0
            padding (10, 10)
            background None
            style "empty"
            vbox:
                spacing 8
                text "Trust: [int(jaily.trust)]" size 18 
                bar value jaily.trust range 100 xmaximum 150
                text "Excitement: [round(jaily.excitement)]" size 18
                bar value jaily.excitement range 100 xmaximum 150
                text "Temperature: [ '{:.2f}'.format(jaily.temperature) ]" size 18
                bar value jaily.temperature range 103.0 xmaximum 150 
                text "Embarrassment: [int(jaily.embarrassment)]" size 18
                bar value jaily.embarrassment range 100 xmaximum 150

screen sequence_display():
    frame:
        xalign 0.5
        yalign 0.1
        background "#00000080"
        padding (10, 10)
        text "[', '.join(current_puzzle.sequence if current_puzzle and hasattr(current_puzzle, 'sequence') else [])]" size 24 color "#ffffff"

screen overheat_overlay():
    zorder 4999
    timer 0.1 action NullAction() repeat True
    $ temp_overlay = jaily.temperature 
    if temp_overlay <= 102.0:
        $ overlay_alpha_val = 0.0
    else:
        $ overlay_alpha_val = (min(temp_overlay, 103.0) - 102.0) * 0.25 
    add Solid("#ff0000", xysize=(config.screen_width, config.screen_height)) alpha overlay_alpha_val

# Utility Labels
label hide_all_ui:
    $ _screens_to_hide = [
        "TouchScreen", 
        "ParticleManagerScreen", 
        "Primary_stats", 
        "sequence_display",
        "overheat_overlay",
        "puzzle_stats_update",
        "game_state_check"
    ]
    python:
        for s_name in _screens_to_hide:
            if renpy.has_screen(s_name): 
                renpy.hide_screen(s_name)
    return

default current_puzzle = None
# Old python block for update_stats.last_time initialization removed
