python early: # Ensure jaily is defined before this runs if particle system needs it immediately
    # This block is moved to the top as per Ren'Py's requirements for python early.
    # It also needs access to JailyState, so JailyState must be defined before or within this block if used here.
    # However, the original Refactor1 defines JailyState much later.
    # This implies 'jaily' might not be truly usable by _particle_system_init_references
    # if that's also in a python early block in another file and expects a fully initialized jaily.
    # For now, just moving the block. The original logic was:
    # if 'jaily' not in globals():
    #    jaily = JailyState() # This would fail if JailyState is not yet defined.
    # Let's assume JailyState will be defined by the time this is needed, or this init is for later.
    # A safer python early block if JailyState is not yet defined would be just:
    # jaily = None
    # And then JailyState() is assigned in the init python block.
    # Given the original code, I will keep its content but log a potential issue.
    if 'jaily' not in globals():
        # If JailyState is defined later in an init python block, this could be problematic
        # or indicates jaily is meant to be globally None initially.
        # For safety in an early block, often we only declare.
        # However, will keep original logic from file for now.
        # If this causes an error, JailyState definition might need to be in a python early block too.
        # For now, to match the structure and intent of the original file:
        pass # Assuming jaily will be properly initialized in a subsequent init python block.
             # The original code had 'jaily = JailyState()' here, which is risky if JailyState isn't known.
             # The prompt's `python early:` block was also inside `init python:`, which is invalid.
             # The most likely intent of such a block (if it were top-level) is to ensure 'jaily' exists.
             # A common pattern is:
             # python early:
             #     jaily = None
             # init python:
             #     class JailyState: ...
             #     jaily = JailyState()
             # I will use this safer pattern for the python early block.
    jaily = None


init python:
    from collections import namedtuple # For Zone
    import random
    import time
    import pygame # For left_mouse_down

    # Initial data structures and generic Puzzle class for CUTSCENE FIX
    Zone = namedtuple("Zone", "x y width height")

    touch_zones = {
        1: { "zone1": Zone(0, 0, 100, 100), "zone2": Zone(200,0,100,100), "locked1": Zone(300,0,50,50) }, # Example for Puzzle 1
        2: { "zone1": Zone(50, 50, 100, 100) }, # Example for Puzzle 2
        # ... add other puzzles as needed
    }

    thresholds = {
        1: { "zone1": 1, "zone2": 1 }, # Example: 1 successful interaction for each zone in Puzzle 1 sequence
        2: { "zone1": 3 }, # Example: 3 successful interactions for zone1 in Puzzle 2
        # ...
    }

    puzzle_times = {
        1: 30, # 30 seconds for Puzzle 1
        2: 45, # 45 seconds for Puzzle 2
        # ...
    }

    puzzle_sequences = {
        1: ["zone1", "zone2", "zone1"], # Sequence for Puzzle 1 - This will be overridden by Puzzle class's sequence
        2: ["zone1"],                    # Sequence for Puzzle 2
        # ... add other puzzle sequences as needed
    }

    # CUTSCENE FIX: Generalized Puzzle class (data model)
    class PuzzleData(object): # Renamed to PuzzleData to avoid conflict with main Puzzle class
        def __init__(self, puzzle_number, zones, thresholds, max_time, sequence_definition):
            self.number = puzzle_number
            self.zones = zones # e.g. touch_zones[puzzle_number]
            self.thresholds = thresholds # e.g. thresholds[puzzle_number]
            self.max_time = max_time # e.g. puzzle_times[puzzle_number]
            self.sequence_definition = sequence_definition # e.g. puzzle_sequences[puzzle_number]
            self.timer = 0
            self.state = {} # To store current progress for each zone, e.g. {"zone1": 0, "zone2": 0}
            for zid in zones:
                self.state[zid] = 0

        def update(self, dt):
            self.timer += dt
            if self.timer > self.max_time:
                return 'timeout' # Puzzle failed due to timeout

            all_zones_complete = True
            for zid, required_amount in self.thresholds.items():
                if self.state.get(zid, 0) < required_amount:
                    all_zones_complete = False
                    break
            if all_zones_complete:
                return 'complete' # Puzzle successfully completed

            return None # Puzzle ongoing

        def process_zone(self, zone_id, amount): # amount can be positive (interaction) or negative (decay)
            if zone_id in self.state:
                self.state[zone_id] += amount

        def is_over(self): # Helper to quickly check if puzzle has a definitive end state
            status = self.update(0)
            return status in ('timeout', 'complete')

    puzzles_data = {}
    for num in touch_zones: # Assuming touch_zones, thresholds, puzzle_times, and puzzle_sequences have the same keys
        if num in puzzle_sequences: # Ensure sequence data exists for the puzzle
            puzzles_data[num] = PuzzleData(
                puzzle_number=num,
                zones=touch_zones[num],
                thresholds=thresholds[num],
                max_time=puzzle_times[num],
                sequence_definition=puzzle_sequences[num] # This sequence might be overridden by the Puzzle class itself
            )
        else:
            renpy.log(f"PuzzleDataSetup: Missing sequence definition for puzzle {num}. Skipping.")

    class JailyState:
        def __init__(self):
            self.trust = 50
            self.excitement = 50
            self.hearts = 50
            self.temperature = 98.6
            self.embarrassment = 50
            self.game_over = False

    jaily = JailyState()

    adjustable_config = {
        "cooldown_duration": 1.0,
        "required_hold_time": 2.0, # This will be used as the target rub duration
        "wrong_grace_period": 5.0,
        "wrong_transition_duration": 1.0,
        "penalty_excitement_rate": 0.05,
        "penalty_trust_rate": 0.05,
        "penalty_embarrassment_rate": 0.05,
        "excitement_increase_rate": 0.02,
        "excitement_decay_rate": 0.01,
        "excitement_stat_baseline": 50,
        "excitement_multiplier_at_min": 0.5,
        "excitement_multiplier_at_max": 1.5,
        "trust_increase_rate": 0.0075,
        "trust_decay_rate": 0.005,
        "trust_stat_baseline": 50,
        "trust_multiplier_at_min": 0.25,
        "trust_multiplier_at_max": 2.0,
        "temp_embarrassment_multiplier": 4.0,
        "temp_incr_rate": 0.05,
        "temp_decay_rate": 0.0025,
        "cooldown_zone_temp_reduction_rate": 0.5,
        "cooldown_zone_excitement_increase_rate": -2.0,
        "chill_penalty_temp_cooldown_rate": 0.2,
        "chill_penalty_excitement_decay_rate": 5.0,
        "chill_penalty_trust_decay_rate": 5.0,
        "temp_lower_game_over": 97.5,
        # New entries for rub mechanic grace period
        "rub_grace_period_min_trust": 1,
        "rub_grace_period_max_trust": 100,
        "rub_grace_period_min_duration": 0.5, # seconds
        "rub_grace_period_max_duration": 2.0, # seconds
    }

    try:
        if 'particle_system' in globals() and hasattr(globals()['particle_system'], '_particle_system_init_references') and callable(globals()['particle_system']._particle_system_init_references):
            particle_system._particle_system_init_references(adjustable_config, jaily)
        elif callable(globals().get('_particle_system_init_references')):
            _particle_system_init_references(adjustable_config, jaily)
        else:
            renpy.log("CRITICAL: Failed to initialize particle system references in Refactor1 logic.")
    except Exception as e:
            renpy.log(f"Error initializing particle system references in Refactor1: {e}")

    # Global input flags for interaction state
    clicked_zone1 = False
    clicked_zone2 = False
    clicked_zone3 = False
    clicked_zone4 = False
    clicked_zone5 = False
    clicked_zone6 = False
    clicked_zone7 = False
    clicked_zone8 = False

    clicked_locked1 = False
    clicked_locked2 = False
    clicked_locked3 = False
    clicked_locked4 = False
    clicked_locked5 = False
    clicked_locked6 = False
    clicked_locked7 = False
    clicked_locked8 = False
    clicked_locked9 = False
    clicked_locked10 = False
    clicked_locked11 = False
    clicked_locked12 = False
    clicked_locked13 = False
    clicked_locked14 = False

    clicked_cooldown = False

    # Global state variables for puzzle interaction (used by Puzzle class methods)
    # These were previously implicitly global or managed by Puzzle instance in Refactor1,
    # explicitly defining them as global here for clarity with new Puzzle class.
    wrong_input_active = False
    wrong_input_start_time = None
    penalty_active = False

    def left_mouse_down():
        return pygame.mouse.get_pressed()[0]

    # Helper function for trust-based grace period
    def get_trust_based_rub_grace_period():
        min_trust = adjustable_config.get("rub_grace_period_min_trust", 1)
        max_trust = adjustable_config.get("rub_grace_period_max_trust", 100)
        min_duration = adjustable_config.get("rub_grace_period_min_duration", 0.5)
        max_duration = adjustable_config.get("rub_grace_period_max_duration", 2.0)

        current_trust = jaily.trust

        if current_trust <= min_trust:
            return min_duration
        if current_trust >= max_trust:
            return max_duration

        # Linear interpolation
        scale_factor = (current_trust - min_trust) / float(max_trust - min_trust)
        grace_duration = min_duration + scale_factor * (max_duration - min_duration)
        return grace_duration

    # New is_interacting function for time-based rub
    def is_interacting(puzzle_instance=None): # Added default to current_puzzle
        target_puzzle = puzzle_instance if puzzle_instance is not None else current_puzzle
        if not target_puzzle:
            return False

        # True if actively rubbing (mouse moving in correct zone) OR if in grace period after leaving zone
        # Ensure all attributes exist on target_puzzle before accessing
        mouse_is_moving = getattr(target_puzzle, 'mouse_is_moving', False)
        current_active_zone = getattr(target_puzzle, 'current_active_zone', None)
        expected_zone = getattr(target_puzzle, 'expected_zone', None)
        current_mouse_pos_tuple = getattr(target_puzzle, 'current_mouse_pos_tuple', None)

        is_rubbing_in_zone = mouse_is_moving and \
                             current_active_zone == expected_zone and \
                             target_puzzle._is_mouse_in_zone_boundary(expected_zone, current_mouse_pos_tuple)

        mouse_outside_zone_grace_period_active_until = getattr(target_puzzle, 'mouse_outside_zone_grace_period_active_until', 0.0)
        is_in_grace_period = mouse_outside_zone_grace_period_active_until > target_puzzle.now_func()

        # Stats should accrue if rubbing in zone, or if grace period is active (implying recent interaction attempt)
        result = is_rubbing_in_zone or is_in_grace_period

        # renpy.log(f"StatDebug: is_interacting: RubbingInZone={is_rubbing_in_zone}, InGracePeriod={is_in_grace_period}, Result={result}")
        return result

    class Puzzle:
        def __init__(self, puzzle_number, puzzle_zones_data=None, now_func=None, mouse_pos_func=None, mouse_down_func=None):
            self.puzzle_number = puzzle_number

            # Zone data for boundary checks
            if puzzle_zones_data is not None: # Direct override for testing
                self.zones_data = puzzle_zones_data
                renpy.log(f"RubDebug: Puzzle {self.puzzle_number} initialized with OVERRIDE zones_data.")
            elif puzzle_number is not None and 'puzzles_data' in globals() and puzzle_number in puzzles_data and hasattr(puzzles_data[puzzle_number], 'zones'):
                self.zones_data = puzzles_data[puzzle_number].zones
                renpy.log(f"RubDebug: Puzzle {self.puzzle_number} loaded zones_data from global puzzles_data.")
            else:
                self.zones_data = {} # Fallback to empty dict if no data found
                renpy.log(f"RubDebug: Warning: Puzzle {self.puzzle_number} could not load zone data. Boundary checks may be unreliable.")

            # Sequence: Longer sequence for rub puzzles
            # This specific sequence overrides any from PuzzleData for this Puzzle class type
            self.sequence = ["zone1", "zone2", "zone1", "zone2", "zone2", "locked1", "zone1", "locked1", "zone2", "locked1"]
            self.current_seq_index = 0
            self.expected_zone = self.sequence[0] if self.sequence else None # Initialize expected_zone

            # Time-based rub attributes
            self.current_rub_time_accumulated = 0.0
            self.last_mouse_pos = None       # Stores tuple (x, y) for movement detection
            self.mouse_is_moving = False     # Flag if mouse moved this frame
            self.mouse_outside_zone_grace_period_active_until = 0.0 # Timestamp
            self.last_rub_update_time = 0.0  # For calculating dt
            self.current_active_zone = None # Track the zone currently being interacted with
            self.current_mouse_pos_tuple = (0,0) # Initialize to a default

            self.cooldown_end_time = 0.0

            # Testability injections
            self.now_func = now_func if callable(now_func) else time.time
            self.mouse_pos_func = mouse_pos_func if callable(mouse_pos_func) else renpy.get_mouse_pos
            self.mouse_down_func = mouse_down_func if callable(mouse_down_func) else left_mouse_down

            self.last_rub_update_time = self.now_func() # Initialize for first dt calculation
            renpy.log(f"RubDebug: Puzzle {self.puzzle_number} initialized. Target rub time: {adjustable_config.get('required_hold_time', 2.0)}s. Zones loaded: {bool(self.zones_data)}. Expected zone: {self.expected_zone}")

        def _is_mouse_in_zone_boundary(self, zone_name, mouse_pos):
            if not self.zones_data or not zone_name: return False
            zone_props = self.zones_data.get(zone_name)
            if not zone_props or not mouse_pos: return False
            # Zone namedtuple is Zone(x, y, width, height)
            x, y, width, height = zone_props.x, zone_props.y, zone_props.width, zone_props.height
            mx, my = mouse_pos
            return x <= mx < x + width and y <= my < y + height

        def rub_timer(self):
            global wrong_input_active, wrong_input_start_time, penalty_active, jaily
            # Clicked flags are needed to determine current_active_zone
            global clicked_zone1, clicked_zone2, clicked_zone3, clicked_zone4, \
                   clicked_zone5, clicked_zone6, clicked_zone7, clicked_zone8, \
                   clicked_locked1, clicked_locked2, clicked_locked3, clicked_locked4, \
                   clicked_locked5, clicked_locked6, clicked_locked7, clicked_locked8, \
                   clicked_locked9, clicked_locked10, clicked_locked11, clicked_locked12, \
                   clicked_locked13, clicked_locked14, clicked_cooldown
            # init_heart_shower_anim might be called
            global init_heart_shower_anim

            now = self.now_func()
            dt = now - self.last_rub_update_time
            self.last_rub_update_time = now

            self.current_mouse_pos_tuple = self.mouse_pos_func()
            current_left_mouse_down = self.mouse_down_func()

            if now < self.cooldown_end_time:
                self.current_active_zone = None; wrong_input_active = False; wrong_input_start_time = None; penalty_active = False
                self.current_rub_time_accumulated = 0.0; self.last_mouse_pos = None; self.mouse_is_moving = False
                self.mouse_outside_zone_grace_period_active_until = 0.0
                return

            if clicked_cooldown and current_left_mouse_down:
                self.current_active_zone = None; wrong_input_active = False; wrong_input_start_time = None; penalty_active = False
                self.current_rub_time_accumulated = 0.0; self.last_mouse_pos = None; self.mouse_is_moving = False
                self.mouse_outside_zone_grace_period_active_until = 0.0
                return

            self.expected_zone = self.sequence[self.current_seq_index] if self.current_seq_index < len(self.sequence) else None

            previous_active_zone = self.current_active_zone # Store for logging if it changed
            new_active_zone_determined_this_frame = None

            if current_left_mouse_down:
                active_flags = {
                    "zone1": clicked_zone1, "zone2": clicked_zone2, "zone3": clicked_zone3, "zone4": clicked_zone4,
                    "zone5": clicked_zone5, "zone6": clicked_zone6, "zone7": clicked_zone7, "zone8": clicked_zone8,
                    "locked1": clicked_locked1, "locked2": clicked_locked2, "locked3": clicked_locked3, "locked4": clicked_locked4,
                    "locked5": clicked_locked5, "locked6": clicked_locked6, "locked7": clicked_locked7, "locked8": clicked_locked8,
                    "locked9": clicked_locked9, "locked10": clicked_locked10, "locked11": clicked_locked11, "locked12": clicked_locked12,
                    "locked13": clicked_locked13, "locked14": clicked_locked14
                }
                if self.expected_zone and active_flags.get(self.expected_zone, False):
                    new_active_zone_determined_this_frame = self.expected_zone
                else:
                    for zone_name, is_clicked_flag in active_flags.items():
                        if is_clicked_flag:
                            new_active_zone_determined_this_frame = zone_name; break

            self.current_active_zone = new_active_zone_determined_this_frame
            # if new_active_zone_determined_this_frame != previous_active_zone:
            #    renpy.log(f"RubDebug: Active zone changed from {previous_active_zone} to {new_active_zone_determined_this_frame}")


            rub_success_this_frame = False
            self.mouse_is_moving = False

            if not current_left_mouse_down:
                if self.current_rub_time_accumulated > 0: renpy.log(f"RubDebug: Mouse UP. Rub time for {previous_active_zone} was {self.current_rub_time_accumulated:.2f}s. Resetting.")
                self.current_rub_time_accumulated = 0.0
                self.last_mouse_pos = None
                self.mouse_outside_zone_grace_period_active_until = 0.0
                self.current_active_zone = None # Ensure active zone is cleared on mouse up
            elif self.current_active_zone == self.expected_zone:
                is_in_bounds = self._is_mouse_in_zone_boundary(self.expected_zone, self.current_mouse_pos_tuple)
                # renpy.log(f"RubDebug: Active on EXPECTED zone {self.expected_zone}. InBounds: {is_in_bounds}. MousePos: {self.current_mouse_pos_tuple}")

                if is_in_bounds:
                    self.mouse_outside_zone_grace_period_active_until = 0.0
                    if self.last_mouse_pos is None:
                        self.last_mouse_pos = self.current_mouse_pos_tuple
                        # renpy.log(f"RubDebug: Rub interaction started/re-entered for {self.expected_zone}.")

                    if self.current_mouse_pos_tuple != self.last_mouse_pos:
                        self.mouse_is_moving = True
                        self.current_rub_time_accumulated += dt
                        # renpy.log(f"RubDebug: MOVING in {self.expected_zone}. AccumulatedTime: {self.current_rub_time_accumulated:.2f}s. dt={dt:.3f}s")
                    # else:
                        # renpy.log(f"RubDebug: STATIONARY in {self.expected_zone}. AccumulatedTime: {self.current_rub_time_accumulated:.2f}s. (Accumulation PAUSED if not moving)")

                    self.last_mouse_pos = self.current_mouse_pos_tuple

                    target_duration = adjustable_config.get("required_hold_time", 2.0) / get_hotzone_multiplier()
                    if self.mouse_is_moving and self.current_rub_time_accumulated >= target_duration: # Only succeed if moving
                        renpy.log(f"RubDebug: SUCCESS on {self.expected_zone}! Accumulated: {self.current_rub_time_accumulated:.2f}s >= Target: {target_duration:.2f}s")
                        rub_success_this_frame = True
                    # else:
                        # renpy.log(f"RubDebug: Ongoing rub on {self.expected_zone}. Accumulated: {self.current_rub_time_accumulated:.2f}s < Target: {target_duration:.2f}s. Moving: {self.mouse_is_moving}")

                else:
                    self.mouse_is_moving = False
                    if self.mouse_outside_zone_grace_period_active_until == 0.0:
                        grace_duration = get_trust_based_rub_grace_period()
                        self.mouse_outside_zone_grace_period_active_until = now + grace_duration
                        renpy.log(f"RubDebug: Mouse LEFT {self.expected_zone} boundary. Grace started for {grace_duration:.2f}s. Rub time {self.current_rub_time_accumulated:.2f}s PAUSED.")
                    elif now > self.mouse_outside_zone_grace_period_active_until:
                        renpy.log(f"RubDebug: Grace period EXPIRED for {self.expected_zone}. Resetting rub time from {self.current_rub_time_accumulated:.2f}s.")
                        self.current_rub_time_accumulated = 0.0
                        self.mouse_outside_zone_grace_period_active_until = 0.0
                    # else:
                        # renpy.log(f"RubDebug: Mouse outside {self.expected_zone}, GRACE PERIOD ACTIVE. Time left: {(self.mouse_outside_zone_grace_period_active_until - now):.2f}s. Rub time {self.current_rub_time_accumulated:.2f}s PAUSED.")
                    self.last_mouse_pos = None

            elif self.current_active_zone is not None and self.current_active_zone != self.expected_zone:
                if not wrong_input_active: wrong_input_start_time = now
                wrong_input_active = True
                renpy.log(f"RubDebug: Interacting with WRONG zone: {self.current_active_zone}. Expected: {self.expected_zone}. Resetting any prior rub attempt.")
                self.current_rub_time_accumulated = 0.0
                self.last_mouse_pos = None
                self.mouse_is_moving = False
                self.mouse_outside_zone_grace_period_active_until = 0.0
            else: # current_active_zone is None (e.g. clicked empty space or mouse up)
                self.mouse_is_moving = False
                if current_left_mouse_down and self.current_rub_time_accumulated > 0 : # Mouse still down but not in a known zone
                     renpy.log(f"RubDebug: Mouse down in NO ZONE, resetting rub time for {previous_active_zone if previous_active_zone else 'previous zone'}.")
                # If mouse is up, this case is also hit, handled by the first `if not current_left_mouse_down:`
                if self.current_rub_time_accumulated > 0 and not current_left_mouse_down: # Covered by first if, but for safety
                    pass # Already logged and reset
                elif current_left_mouse_down : # Mouse is down but not in a tracked zone
                    self.current_rub_time_accumulated = 0.0
                    self.last_mouse_pos = None
                    self.mouse_outside_zone_grace_period_active_until = 0.0


            if rub_success_this_frame:
                self.current_seq_index += 1
                self.cooldown_end_time = now + adjustable_config.get("cooldown_duration", 1.0) / get_hotzone_multiplier()
                if 'init_heart_shower_anim' in globals() and callable(init_heart_shower_anim): init_heart_shower_anim()
                renpy.show_screen("FlashScreen")

                self.current_rub_time_accumulated = 0.0
                self.last_mouse_pos = None
                self.mouse_is_moving = False
                self.mouse_outside_zone_grace_period_active_until = 0.0
                self.expected_zone = self.sequence[self.current_seq_index] if self.current_seq_index < len(self.sequence) else None # Update for next step
                self.current_active_zone = None # Clear active zone after success
                wrong_input_active = False; wrong_input_start_time = None; penalty_active = False
                renpy.log(f"RubDebug: Advancing to sequence index {self.current_seq_index}. Next expected: {self.expected_zone}")


        def update_puzzle_state(self):
            self.rub_timer()

            global wrong_input_active, wrong_input_start_time, penalty_active # Ensure these are accessible
            if not self.mouse_down_func() and wrong_input_active:
                 # renpy.log("RubDebug: Mouse up, global wrong_input_active reset by update_puzzle_state.") # Already logged in rub_timer
                 wrong_input_active = False
                 wrong_input_start_time = None
                 penalty_active = False

            update_stats(is_interacting(self))

        def reset(self):
            renpy.log(f"RubDebug: Puzzle {self.puzzle_number} RESET.")
            self.current_seq_index = 0
            self.current_rub_time_accumulated = 0.0
            self.last_mouse_pos = None
            self.mouse_is_moving = False
            self.mouse_outside_zone_grace_period_active_until = 0.0
            self.cooldown_end_time = 0.0
            self.last_rub_update_time = self.now_func()
            self.expected_zone = self.sequence[0] if self.sequence else None # Reset expected_zone
            self.current_active_zone = None

            global wrong_input_active, wrong_input_start_time, penalty_active # Ensure these are accessible for reset
            wrong_input_active = False; wrong_input_start_time = None; penalty_active = False
            if hasattr(update_stats, 'last_time'): update_stats.last_time = self.now_func()

    current_puzzle = None

    def reset_game():
        global jaily, current_puzzle
        jaily = JailyState()
        if current_puzzle and hasattr(current_puzzle, 'reset'):
            current_puzzle.reset()
        # Initialize current_puzzle to None or a specific puzzle if game starts with one
        # current_puzzle = None # Or Puzzle(puzzle_number=1) for example, if needed at game start

    def puzzle_state_check():
        global jaily, current_puzzle, adjustable_config

        if current_puzzle and hasattr(current_puzzle, 'update_puzzle_state'):
            current_puzzle.update_puzzle_state()

        if jaily.game_over:
            if jaily.temperature >= 103.0: renpy.jump("game_over_max_temp")
            elif jaily.embarrassment >= 100: renpy.jump("game_over_embarrassment")
            elif jaily.trust <= 0: renpy.jump("game_over_trust")
            elif jaily.excitement <= 0: renpy.jump("game_over_excitement")
            elif jaily.temperature <= adjustable_config.get("temp_lower_game_over", 97.5): renpy.jump("game_over_low_temp")
        elif current_puzzle and hasattr(current_puzzle, 'sequence') and \
            current_puzzle.current_seq_index >= len(current_puzzle.sequence):
            renpy.log("RubDebug: Puzzle sequence COMPLETED.")
            renpy.jump("outcome_puzzle")

    # get_hotzone_multiplier and get_trust_penalty_multiplier remain unchanged
    # update_stats remains largely unchanged, but its interacting_flag comes from the new is_interacting

    def get_hotzone_multiplier():
        baseline = adjustable_config.get("excitement_stat_baseline", 50)
        min_mult = adjustable_config.get("excitement_multiplier_at_min", 0.5)
        max_mult = adjustable_config.get("excitement_multiplier_at_max", 1.5)
        excitement = jaily.excitement
        if excitement <= baseline:
            return min_mult + (excitement / baseline) * (1.0 - min_mult) if baseline > 0 else min_mult
        else:
            return 1.0 + ((excitement - baseline) / (100.0 - baseline)) * (max_mult - 1.0) if (100 - baseline) > 0 else 1.0

    def get_trust_penalty_multiplier():
        baseline = adjustable_config.get("trust_stat_baseline", 50)
        min_mult = adjustable_config.get("trust_multiplier_at_min", 0.25)
        max_mult = adjustable_config.get("trust_multiplier_at_max", 2.0)
        trust = jaily.trust
        if trust <= baseline:
            return max_mult + (trust / baseline) * (1.0 - max_mult) if baseline > 0 else max_mult
        else:
            return 1.0 + ((trust - baseline) / (100.0 - baseline)) * (min_mult - 1.0) if (100 - baseline) > 0 else 1.0

    def update_stats(interacting_flag):
        global penalty_active, wrong_input_active, wrong_input_start_time, jaily # Ensure these are accessible
        current_time = time.time() # Using time.time directly, could use current_puzzle.now_func() if puzzle exists

        # Ensure update_stats.last_time exists
        if not hasattr(update_stats, 'last_time'):
            update_stats.last_time = current_time

        dt = current_time - update_stats.last_time
        update_stats.last_time = current_time

        if wrong_input_active and wrong_input_start_time is not None:
            grace_period = adjustable_config.get("wrong_grace_period", 5.0)
            if (current_time - wrong_input_start_time) > grace_period:
                penalty_active = True
            else: # Added else to ensure penalty_active is False during grace period if it was true before
                penalty_active = False
        else: # No wrong input active
             penalty_active = False

        dTemp_calc = adjustable_config.get("temp_incr_rate", 0.05) * (1.0 if interacting_flag else 0.0) - \
                     adjustable_config.get("temp_decay_rate", 0.0025) * (jaily.temperature - 98.6)

        # Embarrassment factor should not make dTemp_calc negative if it was positive, only scale it.
        # Let's ensure embarrassment_factor is at least 1 or appropriately scaled.
        # Original: embarrassment_factor = (jaily.embarrassment / 100.0) * adjustable_config.get("temp_embarrassment_multiplier", 4.0)
        # This could make factor very small if embarrassment is low. Assuming higher embarrassment = higher temp change.
        # A scaling from 1x to X an X might be: 1 + (jaily.embarrassment / 100.0) * (adjustable_config.get("temp_embarrassment_multiplier", 4.0) - 1.0)
        # For now, keeping original logic, but this is a point of review.
        embarrassment_factor = (jaily.embarrassment / 100.0) * adjustable_config.get("temp_embarrassment_multiplier", 4.0)
        embarrassment_factor = max(0.1, embarrassment_factor) # Prevent zero or negative multiplication if temp_incr is positive.

        dTemp_calc *= embarrassment_factor
        jaily.temperature += dTemp_calc * dt

        if penalty_active:
            trust_mult = get_trust_penalty_multiplier()
            exc_change_rate = -adjustable_config.get("penalty_excitement_rate", 0.05) * jaily.excitement * trust_mult
            trust_change_rate = -adjustable_config.get("penalty_trust_rate", 0.05) * jaily.trust * trust_mult
            emb_change_rate = adjustable_config.get("penalty_embarrassment_rate", 0.05) * 100.0 * trust_mult # This seems to intend to increase embarrassment quickly

            jaily.excitement = max(0, jaily.excitement + exc_change_rate * dt)
            jaily.trust = max(0, jaily.trust + trust_change_rate * dt)
            jaily.embarrassment = min(100, jaily.embarrassment + emb_change_rate * dt)
        else:
            interaction_factor_for_stats = 1.0 if interacting_flag else 0.0 # Basic interaction factor

            # This complex factor logic for wrong_input seems to penalize even during grace period for stats.
            # For rub mechanic, simpler might be better: if wrong_input_active, interaction_factor is negative or zero for positive stats.
            # The new is_interacting already handles grace periods for *positive* interaction.
            # If wrong_input_active is true, stats should probably decay or be penalized, not accrue positively.
            if wrong_input_active : # and not penalty_active (i.e. during grace period of wrong input)
                 # If wrong input is active, even in its grace, positive stats shouldn't accrue.
                 # Setting interaction_factor to 0 or negative.
                 interaction_factor_for_stats = 0 # Or a negative value if decay is desired during wrong_input grace.

            temp_factor = 1 + (jaily.temperature - 98.6) / (103.0 - 98.6) # Assuming 103 is a high temp benchmark
            temp_factor = max(0.5, min(temp_factor, 2.0)) # Clamp temp_factor to avoid extreme values

            exc_change_rate = adjustable_config.get("excitement_increase_rate",0.02) * jaily.trust * interaction_factor_for_stats * temp_factor - \
                              adjustable_config.get("excitement_decay_rate",0.01) * jaily.excitement
            jaily.excitement = min(100, max(0, jaily.excitement + exc_change_rate * dt))

            trust_change_rate = adjustable_config.get("trust_increase_rate",0.0075) * jaily.excitement * interaction_factor_for_stats * temp_factor - \
                                adjustable_config.get("trust_decay_rate",0.005) * (jaily.trust - adjustable_config.get("trust_stat_baseline",50))
            jaily.trust = min(100, max(0, jaily.trust + trust_change_rate * dt))

        # Cooldown zone logic
        if clicked_cooldown and left_mouse_down():
            if jaily.temperature > 98.5: # Assuming 98.5 is a threshold for beneficial cooldown
                jaily.temperature -= adjustable_config.get("cooldown_zone_temp_reduction_rate",0.5) * dt
                jaily.excitement += adjustable_config.get("cooldown_zone_excitement_increase_rate",-2.0) * dt # Negative rate implies decrease
            else: # Penalty for using cooldown when not hot
                jaily.temperature -= adjustable_config.get("chill_penalty_temp_cooldown_rate",0.2) * dt
                jaily.excitement -= adjustable_config.get("chill_penalty_excitement_decay_rate",5.0) * dt
                jaily.trust -= adjustable_config.get("chill_penalty_trust_decay_rate",5.0) * dt
            jaily.excitement = min(100,max(0,jaily.excitement))
            jaily.trust = min(100,max(0,jaily.trust))

        # Game Over checks
        if (jaily.temperature >= 103.0 or jaily.embarrassment >= 100 or \
            jaily.trust <= 0 or jaily.excitement <= 0 or \
            jaily.temperature <= adjustable_config.get("temp_lower_game_over", 97.5)):
            jaily.game_over = True


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

screen puzzle_stats_update():
    # timer 0.016 action Function(lambda: update_stats(is_interacting())) repeat True
    # The is_interacting() call needs current_puzzle, if it's available
    # This screen might be too early for current_puzzle to be reliably set.
    # update_stats is now called from Puzzle.update_puzzle_state which is called by game_state_check timer.
    # So this screen might be redundant or could be removed if stats are solely updated via game_state_check.
    # For now, commenting out its action to avoid potential double calls or errors.
    # If it is needed, ensure is_interacting() can handle current_puzzle being None early on.
    timer 0.016 action NullAction() repeat True # Or Function(lambda: update_stats(is_interacting(current_puzzle)))

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
                bar value jaily.temperature range 103.0 xmaximum 150 # Max range of bar could be higher like 105
                text "Embarrassment: [int(jaily.embarrassment)]" size 18
                bar value jaily.embarrassment range 100 xmaximum 150

screen sequence_display():
    frame:
        xalign 0.5
        yalign 0.1
        background "#00000080"
        padding (10, 10)
        # Ensure current_puzzle and its sequence attribute exist
        $ seq_text = ", ".join(current_puzzle.sequence) if current_puzzle and hasattr(current_puzzle, 'sequence') and current_puzzle.sequence else "No sequence"
        text "[seq_text]" size 24 color "#ffffff"


screen overheat_overlay():
    zorder 4999
    timer 0.1 action NullAction() repeat True
    $ temp_overlay = jaily.temperature if jaily is not None else 98.6
    if temp_overlay <= 102.0: # Threshold for visual effect
        $ overlay_alpha_val = 0.0
    else:
        # Scale from 0 to 0.25 alpha as temp goes from 102.0 to 103.0 (or higher, capped at 103 for this calc)
        $ overlay_alpha_val = (min(temp_overlay, 103.0) - 102.0) * 0.25
    add Solid("#ff0000", xysize=(config.screen_width, config.screen_height)) alpha overlay_alpha_val

label hide_all_ui:
    $ _screens_to_hide = [
        "ParticleManagerScreen",
        "Primary_stats",
        "sequence_display",
        "overheat_overlay",
        "puzzle_stats_update", # May or may not be active
        "game_state_check" # This timer screen should typically not be hidden if it drives core logic
    ]
    python:
        for s_name in _screens_to_hide:
            if renpy.has_screen(s_name):
                if s_name == "game_state_check" or s_name == "puzzle_stats_update": # Be cautious
                    renpy.log(f"HideDebug: UI hide requested to hide timer screen {s_name}. Consider if this is intended.")
                renpy.hide_screen(s_name)
    return
