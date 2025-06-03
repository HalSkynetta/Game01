# This file will contain all particle system related code.

init python:
    import random
    import time
    # pygame is implicitly available in Ren'Py for renpy.get_mouse_pos()
    # No direct import of pygame needed here unless other pygame features are used.

    # Particle-specific configurations extracted from the main adjustable_config
    adjustable_config_particles = {
        # Hearts Particle CONFIG
        "hearts_threshold": 25,
        "hearts_lower_bound": 30,
        "hearts_upper_bound": 100,
        "pps_at_lower_bound_hearts": 0.5,
        "pps_at_upper_bound_hearts": 10.0,

        # Trust Particle Ranges
        "trust_threshold": 31,
        "trust_lower_bound": 51, # Used by compute_trust_pps
        "trust_upper_bound": 100, # Used by compute_trust_pps
        "pps_at_lower_bound_trust": 0.20,
        "pps_at_upper_bound_trust": 0.5,
        "trust_particle_phase_offset": 0.5, # Moved as it's used in ParticleManager init for trust_accumulator

        # Excitement Particle Ranges
        "excitement_threshold": 25,
        "excitement_lower_bound": 30, # Used by compute_pps
        "excitement_upper_bound": 100, # Used by compute_pps
        "pps_at_lower_bound": 0.20,   # For excitement particles
        "pps_at_upper_bound": 0.5,    # For excitement particles

        "particle_transition_duration": 5.0,  # How long it takes to adjust particle rate
        "particle_update_interval": 0.016,    # Particle update frequency (~60fps)

        # Heart shower adjustable attributes
        "heart_shower": {
            "duration": 3.0,            # Duration in seconds for the shower animation
            "heart_count": 100,         # Number of hearts spawned
            "x_start_min": -100,        # Minimum starting x position
            "x_start_max": 2020,         # Maximum starting x position
            "y_start_min": -200,        # Minimum starting y position
            "y_start_max": 0,           # Maximum starting y position
            "x_end_min": -100,          # Minimum ending x position
            "x_end_max": 2020,           # Maximum ending x position
            "y_end_min": 1180,          # Minimum ending y position
            "y_end_max": 2400,           # Maximum ending y position
            "rotation_min": -30,        # Minimum rotation in degrees
            "rotation_max": 30,         # Maximum rotation in degrees
            "scale_min": 0.75,          # Minimum scale factor
            "scale_max": 3.0            # Maximum scale factor
        }
    }

    # Precomputed Heart Shower Animation Data
    heart_shower_anim = []
    def init_heart_shower_anim():
        global heart_shower_anim
        # Ensure this uses the local particle config
        hs = adjustable_config_particles["heart_shower"]
        heart_shower_anim = []
        for i in range(hs["heart_count"]):
            data = {}
            data["x_start"] = random.randint(hs["x_start_min"], hs["x_start_max"])
            data["y_start"] = random.randint(hs["y_start_min"], hs["y_start_max"])
            data["x_end"] = random.randint(hs["x_end_min"], hs["x_end_max"])
            data["y_end"] = random.randint(hs["y_end_min"], hs["y_end_max"])
            data["r_rotate"] = random.randint(hs["rotation_min"], hs["rotation_max"])
            data["r_scale"] = random.uniform(hs["scale_min"], hs["scale_max"])
            # Assuming image definitions like "Hearts_A" are globally available or handled elsewhere
            data["heart_img"] = random.choice(["Hearts_A", "Hearts_B"])
            heart_shower_anim.append(data)

    # Particle Spawn Rate Functions
    # These functions now use adjustable_config_particles
    def compute_pps(excitement): # Excitement particles
        if excitement <= adjustable_config_particles["excitement_threshold"]:
            return 0.0
        elif excitement < adjustable_config_particles["excitement_lower_bound"]:
            return ((excitement - adjustable_config_particles["excitement_threshold"]) /
                    (adjustable_config_particles["excitement_lower_bound"] - adjustable_config_particles["excitement_threshold"])
                   ) * adjustable_config_particles["pps_at_lower_bound"]
        else:
            ratio = (excitement - adjustable_config_particles["excitement_lower_bound"]) / (adjustable_config_particles["excitement_upper_bound"] - adjustable_config_particles["excitement_lower_bound"])
            return adjustable_config_particles["pps_at_lower_bound"] + ratio * (adjustable_config_particles["pps_at_upper_bound"] - adjustable_config_particles["pps_at_lower_bound"])

    def compute_trust_pps(trust):
        if trust <= adjustable_config_particles["trust_threshold"]:
            return 0.0
        elif trust < adjustable_config_particles["trust_lower_bound"]:
            return ((trust - adjustable_config_particles["trust_threshold"]) /
                    (adjustable_config_particles["trust_lower_bound"] - adjustable_config_particles["trust_threshold"])
                   ) * adjustable_config_particles["pps_at_lower_bound_trust"]
        else:
            ratio = (trust - adjustable_config_particles["trust_lower_bound"]) / (adjustable_config_particles["trust_upper_bound"] - adjustable_config_particles["trust_lower_bound"])
            return adjustable_config_particles["pps_at_lower_bound_trust"] + ratio * (adjustable_config_particles["pps_at_upper_bound_trust"] - adjustable_config_particles["pps_at_lower_bound_trust"])

    def compute_hearts_pps(hearts):
        if hearts <= adjustable_config_particles["hearts_threshold"]:
            return 0.0
        elif hearts < adjustable_config_particles["hearts_lower_bound"]:
            return ((hearts - adjustable_config_particles["hearts_threshold"]) /
                    (adjustable_config_particles["hearts_lower_bound"] - adjustable_config_particles["hearts_threshold"])
                   ) * adjustable_config_particles["pps_at_lower_bound_hearts"]
        else:
            ratio = (hearts - adjustable_config_particles["hearts_lower_bound"]) / (adjustable_config_particles["hearts_upper_bound"] - adjustable_config_particles["hearts_lower_bound"])
            return adjustable_config_particles["pps_at_lower_bound_hearts"] + ratio * (adjustable_config_particles["pps_at_upper_bound_hearts"] - adjustable_config_particles["pps_at_lower_bound_hearts"])

    # Particle Configurations and Lists
    particles = []              # For heart particles (general interaction)
    excitement_particles = []   # For excitement state
    trust_particles = []        # For trust state

    particle_config = { # For general heart particles
        "particles_per_sec": 0, # Dynamically updated by ParticleManager
        "lifetime": 1.1,
        "fadeout_start": 0.1,
        "size_range": (0.9, 1.25),
        "size_multiplier": 1.0,
        "rotation_range": (-45, 45),
        "spread_range": (-150, 150)
    }

    particle_config_excitement = { # For excitement particles
        "particles_per_sec": 0, # Dynamically updated by ParticleManager
        "lifetime": 2.5,
        "fadeout_start": 2.0,
        "size_range": (0.9, 1.1),
        "size_multiplier": 0.75,
        "rotation_range": (-7, 7),
        "spread_range": (-200, 200)
    }

    particle_config_trust = { # For trust particles
        "particles_per_sec": 0, # Dynamically updated by ParticleManager
        "lifetime": 2.5,
        "fadeout_start": 2.0,
        "size_range": (0.9, 1.1),
        "size_multiplier": 0.75,
        "rotation_range": (-7, 7),
        "spread_range": (-200, 200)
    }
    
    # External state dependencies that these functions use.
    jaily = None 
    penalty_active = False
    wrong_input_active = False
    wrong_input_start_time = None

    # Particle Functions
    def spawn_particle(pos): 
        p = {}
        if penalty_active or (wrong_input_active and wrong_input_start_time and (time.time() - wrong_input_start_time >= adjustable_config.get("wrong_grace_period", 5.0))):
            p['heart'] = random.choice(["Hearts_C", "Hearts_D"]) 
        else:
            p['heart'] = random.choice(["Hearts_A", "Hearts_B"]) 
        p['x'] = pos[0] + random.randint(*particle_config["spread_range"])
        p['y'] = pos[1] + random.randint(*particle_config["spread_range"])
        p['zoom'] = random.uniform(*particle_config["size_range"]) * particle_config["size_multiplier"]
        p['rotate'] = random.randint(*particle_config["rotation_range"])
        p['spawn_time'] = time.time()
        particles.append(p)

    def spawn_excitement_particle(pos):
        global jaily 
        p = {}
        exp = jaily.excitement if jaily else 0
        if 55 <= exp <= 74:
            p['image'] = random.choice(["Excitement_A", "Excitement_B"])
        elif 75 <= exp <= 94:
            p['image'] = random.choice(["Excitement_C", "Excitement_D"])
        elif 95 <= exp <= 100:
            p['image'] = random.choice(["Excitement_E", "Excitement_F"])
        else:
            return
        p['x'] = pos[0] + random.randint(*particle_config_excitement["spread_range"])
        p['y'] = pos[1] + random.randint(*particle_config_excitement["spread_range"])
        p['zoom'] = random.uniform(*particle_config_excitement["size_range"]) * particle_config_excitement["size_multiplier"]
        p['rotate'] = random.randint(*particle_config_excitement["rotation_range"])
        p['spawn_time'] = time.time()
        excitement_particles.append(p)

    def spawn_trust_particle(pos):
        global jaily 
        p = {}
        tr = jaily.trust if jaily else 0
        ab_low, ab_high = adjustable_config.get("trust_range_ab", (55, 74))
        cd_low, cd_high = adjustable_config.get("trust_range_cd", (75, 94))
        ef_low, ef_high = adjustable_config.get("trust_range_ef", (95, 100))
        if ab_low <= tr <= ab_high:
            p['image'] = random.choice(["Trust_A", "Trust_B"])
        elif cd_low <= tr <= cd_high:
            p['image'] = random.choice(["Trust_C", "Trust_D"])
        elif ef_low <= tr <= ef_high:
            p['image'] = random.choice(["Trust_E", "Trust_F"])
        else:
            return
        p['x'] = pos[0] + random.randint(*particle_config_trust["spread_range"])
        p['y'] = pos[1] + random.randint(*particle_config_trust["spread_range"])
        p['zoom'] = random.uniform(*particle_config_trust["size_range"]) * particle_config_trust["size_multiplier"]
        p['rotate'] = random.randint(*particle_config_trust["rotation_range"])
        p['spawn_time'] = time.time()
        trust_particles.append(p)

    def cleanup_particles():
        now = time.time()
        particles[:] = [p for p in particles if now - p['spawn_time'] < particle_config["lifetime"]]
        excitement_particles[:] = [p for p in excitement_particles if now - p['spawn_time'] < particle_config_excitement["lifetime"]]
        trust_particles[:] = [p for p in trust_particles if now - p['spawn_time'] < particle_config_trust["lifetime"]]

    class ParticleManager:
        def __init__(self):
            global jaily 
            self.heart_accumulator = 0.0
            self.excitement_accumulator = 0.0
            initial_trust_pps = compute_trust_pps(jaily.trust if jaily else 0)
            if initial_trust_pps > 0:
                initial_spawn_interval = 1.0 / initial_trust_pps
                self.trust_accumulator = initial_spawn_interval * adjustable_config_particles["trust_particle_phase_offset"]
            else:
                self.trust_accumulator = 0.0
            self.last_time = time.time()

        def update(self):
            global jaily, clicked_zone1, clicked_zone2, clicked_zone3, clicked_zone4, \
                   clicked_zone5, clicked_zone6, clicked_zone7, clicked_zone8, \
                   clicked_locked1, clicked_locked2, clicked_locked3, clicked_locked4, \
                   clicked_locked5, clicked_locked6, clicked_locked7, clicked_locked8, \
                   clicked_locked9, clicked_locked10, clicked_locked11, clicked_locked12, \
                   clicked_locked13, clicked_locked14, clicked_cooldown, left_mouse_down

            current_time = time.time()
            dt = current_time - self.last_time
            self.last_time = current_time # Moved this line up

            interacting_for_particles = (clicked_zone1 or clicked_zone2 or clicked_zone3 or clicked_zone4 or
                                       clicked_zone5 or clicked_zone6 or clicked_zone7 or clicked_zone8 or
                                       clicked_locked1 or clicked_locked2 or clicked_locked3 or clicked_locked4 or
                                       clicked_locked5 or clicked_locked6 or clicked_locked7 or clicked_locked8 or
                                       clicked_locked9 or clicked_locked10 or clicked_locked11 or clicked_locked12 or
                                       clicked_locked13 or clicked_locked14 or clicked_cooldown) and left_mouse_down() if callable(left_mouse_down) else False
            
            if interacting_for_particles:
                current_mouse_pos = renpy.get_mouse_pos() 

                self.heart_accumulator += dt
                spawn_interval = 1.0 / max(1e-6, particle_config["particles_per_sec"])
                while self.heart_accumulator >= spawn_interval:
                    spawn_particle(current_mouse_pos) 
                    self.heart_accumulator -= spawn_interval

                if 55 <= (jaily.excitement if jaily else 0) <= 100:
                    self.excitement_accumulator += dt
                    spawn_interval_excitement = 1.0 / max(1e-6, particle_config_excitement["particles_per_sec"])
                    while self.excitement_accumulator >= spawn_interval_excitement:
                        spawn_excitement_particle(current_mouse_pos) 
                        self.excitement_accumulator -= spawn_interval_excitement
                else:
                    self.excitement_accumulator = 0.0

                if 55 <= (jaily.trust if jaily else 0) <= 100:
                    self.trust_accumulator += dt
                    spawn_interval_trust = 1.0 / max(1e-6, particle_config_trust["particles_per_sec"])
                    while self.trust_accumulator >= spawn_interval_trust:
                        spawn_trust_particle(current_mouse_pos) 
                        self.trust_accumulator -= spawn_interval_trust
                else:
                    self.trust_accumulator = 0.0
            else:
                self.heart_accumulator = 0.0
                self.excitement_accumulator = 0.0
                initial_trust_pps = compute_trust_pps(jaily.trust if jaily else 0)
                if initial_trust_pps > 0:
                    initial_spawn_interval = 1.0 / initial_trust_pps
                    self.trust_accumulator = initial_spawn_interval * adjustable_config_particles["trust_particle_phase_offset"]
                else:
                    self.trust_accumulator = 0.0

            target_hearts_particles = compute_hearts_pps(jaily.hearts if jaily else 0) 
            current_hearts_particles = particle_config["particles_per_sec"] 
            transition_rate_hearts = adjustable_config_particles["pps_at_lower_bound_hearts"] / adjustable_config_particles["particle_transition_duration"]
            if current_hearts_particles < target_hearts_particles:
                current_hearts_particles = min(target_hearts_particles, current_hearts_particles + transition_rate_hearts * dt)
            elif current_hearts_particles > target_hearts_particles:
                current_hearts_particles = max(target_hearts_particles, current_hearts_particles - transition_rate_hearts * dt)
            particle_config["particles_per_sec"] = current_hearts_particles

            target_particles = compute_pps(jaily.excitement if jaily else 0) 
            current_particles = particle_config_excitement["particles_per_sec"] 
            transition_rate = adjustable_config_particles["pps_at_lower_bound"] / adjustable_config_particles["particle_transition_duration"]
            if current_particles < target_particles:
                current_particles = min(target_particles, current_particles + transition_rate * dt)
            elif current_particles > target_particles:
                current_particles = max(target_particles, current_particles - transition_rate * dt)
            particle_config_excitement["particles_per_sec"] = current_particles

            target_trust_particles = compute_trust_pps(jaily.trust if jaily else 0) 
            current_trust_particles = particle_config_trust["particles_per_sec"] 
            transition_rate_trust = adjustable_config_particles["pps_at_lower_bound_trust"] / adjustable_config_particles["particle_transition_duration"]
            if current_trust_particles < target_trust_particles:
                current_trust_particles = min(target_trust_particles, current_trust_particles + transition_rate_trust * dt)
            elif current_trust_particles > target_trust_particles:
                current_trust_particles = max(target_trust_particles, current_trust_particles - transition_rate_trust * dt)
            particle_config_trust["particles_per_sec"] = current_trust_particles

            # self.last_time = current_time # Moved up

    particle_manager = ParticleManager()

    def update_particle_system():
        particle_manager.update()

# Particle-related Screens and Transforms
transform heart_shower(x_start, y_start, x_end, y_end, rotate, scale):
    pos (x_start, y_start)
    rotate rotate
    zoom scale
    alpha 1.0
    linear adjustable_config_particles["heart_shower"]["duration"]:
         pos (x_end, y_end)
         alpha 0.0

screen FlashScreen():
    modal False
    zorder 5000
    timer adjustable_config_particles["heart_shower"]["duration"] action Hide("FlashScreen")
    for data in heart_shower_anim: 
        add data["heart_img"] at heart_shower(data["x_start"], data["y_start"], data["x_end"], data["y_end"], data["r_rotate"], data["r_scale"])

screen particles_screen():
    zorder 2000
    timer 0.1 action Function(cleanup_particles) repeat True
    for p in particles:
        $ age = time.time() - p['spawn_time']
        $ current_alpha = 1.0 if age < particle_config["fadeout_start"] else ((particle_config["lifetime"] - age) / max(0.001, (particle_config["lifetime"] - particle_config["fadeout_start"])))
        add p['heart'] at Transform( 
            anchor=(0.5, 0.5),
            pos=(p['x'], p['y']),
            zoom=p['zoom'],
            rotate=p['rotate'],
            alpha=current_alpha
        )
    for p in excitement_particles:
        $ age = time.time() - p['spawn_time']
        $ current_alpha = 1.0 if age < particle_config_excitement["fadeout_start"] else ((particle_config_excitement["lifetime"] - age) / max(0.001, (particle_config_excitement["lifetime"] - particle_config_excitement["fadeout_start"])))
        add p['image'] at Transform( 
            anchor=(0.5, 0.5),
            pos=(p['x'], p['y']),
            zoom=p['zoom'],
            rotate=p['rotate'],
            alpha=current_alpha
        )
    for p in trust_particles:
        $ age = time.time() - p['spawn_time']
        $ current_alpha = 1.0 if age < particle_config_trust["fadeout_start"] else ((particle_config_trust["lifetime"] - age) / max(0.001, (particle_config_trust["lifetime"] - particle_config_trust["fadeout_start"])))
        add p['image'] at Transform( 
            anchor=(0.5, 0.5),
            pos=(p['x'], p['y']),
            zoom=p['zoom'],
            rotate=p['rotate'],
            alpha=current_alpha
        )

screen ParticleManagerScreen():
    zorder 1000
    timer adjustable_config_particles["particle_update_interval"] action Function(update_particle_system) repeat True

python:
    def _particle_system_init_references(main_adjustable_config, main_jaily_state):
        global adjustable_config, jaily
        adjustable_config = main_adjustable_config
        jaily = main_jaily_state
    pass

