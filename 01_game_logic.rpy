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
    # Modified to call the Puzzle class's is_interacting method.
    def is_interacting(puzzle_instance=None): # Keep signature for compatibility
        target_puzzle = puzzle_instance if puzzle_instance is not None else current_puzzle
        if target_puzzle and hasattr(target_puzzle, 'is_interacting') and callable(getattr(target_puzzle, 'is_interacting')):
            return target_puzzle.is_interacting()
        # renpy.log("GlobalIsInteractingDebug: current_puzzle or its method not available.")
        return False

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

            # Time-based interaction attributes (replacing/evolving from just_hit_zone)
            # self.just_hit_zone = False # Removed as per new requirements
            self.current_active_zone = None # Track the zone currently being interacted with
            self.current_mouse_pos_tuple = (0,0) # Initialize to a default
            
            self.current_hold_time_accumulated = 0.0
            self.is_actively_holding_expected_zone = False
            self.hold_start_time = 0.0
            self.hold_started_on_expected_zone = False

            self.cooldown_end_time = 0.0

            # Testability injections
            self.now_func = now_func if callable(now_func) else time.time
            self.mouse_pos_func = mouse_pos_func if callable(mouse_pos_func) else renpy.get_mouse_pos
            self.mouse_down_func = mouse_down_func if callable(mouse_down_func) else left_mouse_down

            # self.last_rub_update_time = self.now_func() # Initialize for first dt calculation # Removed
            renpy.log(f"RubDebug: Puzzle {self.puzzle_number} initialized. Zones loaded: {bool(self.zones_data)}. Expected zone: {self.expected_zone}")

        def _is_mouse_in_zone_boundary(self, zone_name, mouse_pos):
            if not self.zones_data or not zone_name: return False
            zone_props = self.zones_data.get(zone_name)
            if not zone_props or not mouse_pos: return False
            # Zone namedtuple is Zone(x, y, width, height)
            x, y, width, height = zone_props.x, zone_props.y, zone_props.width, zone_props.height
            mx, my = mouse_pos
            return x <= mx < x + width and y <= my < y + height

        def update_interaction_logic(self):
            mouse_pos = self.mouse_pos_func()
            left_mouse_is_down = self.mouse_down_func()
            # Ensure global flags are accessible for modification
            global wrong_input_active, wrong_input_start_time, penalty_active, jaily, init_heart_shower_anim

            current_hovered_zone_id = None
            if self.zones_data: # Check if zones_data is loaded
                for zid in self.zones_data.keys():
                    global_flag_name = f"clicked_{zid}"
                    if globals().get(global_flag_name, False):
                        current_hovered_zone_id = zid
                        break
            
            was_actively_holding = self.is_actively_holding_expected_zone # Ensure this line is present

            if left_mouse_is_down:
                if not self.is_actively_holding_expected_zone: # Potential start of a new hold
                    # **** NEW CODE START ****
                    if current_hovered_zone_id is not None:
                        # Ensure spawn_particle is globally available or imported.
                        # We assume it is, as per Ren'Py's typical behavior for functions in init python blocks.
                        if 'spawn_particle' in globals() and callable(globals()['spawn_particle']):
                            globals()['spawn_particle'](mouse_pos)
                        else:
                            renpy.log("Warning: spawn_particle function not found for click.")
                    # **** NEW CODE END ****

                    if current_hovered_zone_id == self.expected_zone and self.now_func() >= self.cooldown_end_time:
                        # Start a new hold
                        self.is_actively_holding_expected_zone = True
                        renpy.log(f"HoldStateChange: is_actively_holding_expected_zone SET TRUE. Hold started on: {self.expected_zone}")
                        self.hold_started_on_expected_zone = True # Mark that this hold started correctly
                        self.hold_start_time = self.now_func()
                        self.current_hold_time_accumulated = 0.0
                        # renpy.log(f"PuzzleDebug: Hold STARTED on {self.expected_zone}") # Covered by HoldStateChange
                        wrong_input_active = False # Starting correct hold clears wrong input state
                        wrong_input_start_time = None 
                        penalty_active = False
                    elif current_hovered_zone_id is not None: # Pressed a wrong zone (or correct zone on cooldown)
                        if self.now_func() >= self.cooldown_end_time: # Only set wrong_input if not in general cooldown
                            if not wrong_input_active: # Set start time only if not already in a wrong_input state from a previous frame
                                wrong_input_start_time = self.now_func()
                            wrong_input_active = True
                            renpy.log(f"PuzzleDebug: Pressed WRONG zone {current_hovered_zone_id} or expected zone {self.expected_zone} during its cooldown.")
                        # Ensure any previous (now invalid) hold state is cleared
                        if self.is_actively_holding_expected_zone: # Log only if it was true
                            renpy.log(f"HoldStateChange: is_actively_holding_expected_zone SET FALSE. Reason: Invalid press on {current_hovered_zone_id} or cooldown.")
                        self.is_actively_holding_expected_zone = False
                        self.hold_started_on_expected_zone = False
                        self.current_hold_time_accumulated = 0.0
                    else: # Pressed an empty area
                        if self.is_actively_holding_expected_zone: # Log only if it was true
                             renpy.log(f"HoldStateChange: is_actively_holding_expected_zone SET FALSE. Reason: Pressed empty area.")
                        self.is_actively_holding_expected_zone = False
                        self.hold_started_on_expected_zone = False
                        self.current_hold_time_accumulated = 0.0

                # If currently holding (either just started or continuing)
                if self.is_actively_holding_expected_zone:
                    if current_hovered_zone_id == self.expected_zone: # Still on the correct zone
                        self.current_hold_time_accumulated = self.now_func() - self.hold_start_time
                        
                        # Check for SUCCESS while button is still down
                        target_duration = max(adjustable_config.get("required_hold_time", 5.0), 3.0) / get_hotzone_multiplier()

                        # Ensure jaily is accessible, it should be global
                        # Ensure get_hotzone_multiplier is accessible, it's a global function
                        # Ensure adjustable_config is accessible, it's a global dict
                        current_excitement = jaily.excitement if 'jaily' in globals() and hasattr(jaily, 'excitement') else -1
                        current_multiplier = get_hotzone_multiplier() if 'get_hotzone_multiplier' in globals() else -1
                        config_hold_time = adjustable_config.get('required_hold_time', 2.0) if 'adjustable_config' in globals() else -1

                        renpy.log(f"DurationCheck: Excitement={current_excitement}, Multiplier={current_multiplier:.2f}, ConfigHoldTime={config_hold_time:.2f}, TargetDuration={target_duration:.2f}, Accumulated={self.current_hold_time_accumulated:.2f}")
                        
                        if self.current_hold_time_accumulated >= target_duration:
                            renpy.log(f"PuzzleDebug: SUCCESS on {self.expected_zone}! Hold time: {self.current_hold_time_accumulated:.2f}s. Button still HELD.")
                            # "Hit" processing:
                            self.current_seq_index += 1
                            self.cooldown_end_time = self.now_func() + adjustable_config.get("cooldown_duration", 1.0) / get_hotzone_multiplier()
                            if 'init_heart_shower_anim' in globals() and callable(globals()['init_heart_shower_anim']):
                                globals()['init_heart_shower_anim']()
                            renpy.show_screen("FlashScreen")
                            self.expected_zone = self.sequence[self.current_seq_index] if self.current_seq_index < len(self.sequence) else None
                            
                            # Reset hold state immediately after success to prevent re-triggering until mouse is released and pressed again
                            renpy.log(f"HoldStateChange: is_actively_holding_expected_zone SET FALSE. Reason: Success triggered for {self.expected_zone}.") # Log before reset
                            self.is_actively_holding_expected_zone = False
                            self.hold_started_on_expected_zone = False
                            self.current_hold_time_accumulated = 0.0
                            
                            wrong_input_active = False # Successful interaction
                            wrong_input_start_time = None
                            penalty_active = False
                    else: # Moved off the expected zone while holding
                        renpy.log(f"HoldStateChange: is_actively_holding_expected_zone SET FALSE. Reason: Moved off zone. Was holding: {self.expected_zone if self.hold_started_on_expected_zone else 'N/A'}")
                        # renpy.log(f"PuzzleDebug: Hold INTERRUPTED on {self.expected_zone} (moved off zone). Accumulated: {self.current_hold_time_accumulated:.2f}s") # More detailed log covered by HoldStateChange
                        self.is_actively_holding_expected_zone = False
                        self.hold_started_on_expected_zone = False
                        # self.current_hold_time_accumulated = 0.0 # Reset time; it will be 0 on next valid start
                        # Do NOT set wrong_input_active here, as simply moving off isn't a "wrong click".
                        # If they click elsewhere, that will trigger wrong_input. If they release, nothing happens.

            else: # Mouse button is UP
                if self.hold_started_on_expected_zone: # Was holding the correct zone, but released before success trigger (e.g. too early or moved off)
                    renpy.log(f"PuzzleDebug: Mouse RELEASED from what was a correctly initiated hold on {self.expected_zone}. Last accumulated time: {self.current_hold_time_accumulated:.2f}s. Success already triggered: no.")
                    # This state means the hold was validly started, but mouse was released *before* time condition was met OR *after* moving off zone.
                    # If success happens while HELD, then self.hold_started_on_expected_zone would be false by the time of release.
                    # So this implies a failed attempt.
                    # However, if they just moved off and released, we don't want to penalize with wrong_input_active.
                    # If they released on the zone too early, it's a failed attempt.
                    # The current logic doesn't distinguish release on vs off zone if success isn't met.
                    # For now, just resetting states is fine, as wrong_input_active is not set here.
                    pass


                # Reset all per-hold attempt states now that mouse is up
                if was_actively_holding : # Log only if it was true before this block and is being set to false now.
                    renpy.log(f"HoldStateChange: is_actively_holding_expected_zone SET FALSE. Reason: Mouse button up. Was holding: {self.expected_zone if self.hold_started_on_expected_zone else 'N/A'}")
                self.is_actively_holding_expected_zone = False
                self.current_hold_time_accumulated = 0.0
                self.hold_started_on_expected_zone = False
                # Note: wrong_input_active is NOT reset here by default by this specific block.
                # It's reset on a new VALID hold start, or by update_stats timeout, or on success.
            
            # renpy.log(f"PuzzleState: HoldingExpected: {self.is_actively_holding_expected_zone}, AccumTime: {self.current_hold_time_accumulated:.2f}, WrongInput: {wrong_input_active}")

        def is_interacting(self):
            # This method is used by update_stats.
            # It should return True if the player is currently successfully holding down on the target zone.
            # self.is_actively_holding_expected_zone is set to True when a hold starts correctly 
            # and mouse is on the expected zone, and set to False if interrupted or mouse moves off.
            # It's also reset immediately after a successful trigger to prevent re-triggering or 
            # continuous stat accrual after success on the same press.
            # However, for stat accrual, we care if they are *still* on the zone *after* a successful trigger,
            # if the hold *could* continue.
            # The current definition of self.is_actively_holding_expected_zone is reset upon success.
            # This means stats would stop accruing immediately at the point of success.
            # Let's reconsider: update_stats should reflect the state *leading to* or *during* interaction.
            # If self.is_actively_holding_expected_zone is true, it means they are in a valid, ongoing hold.

            # Correct logic: simply return the state of self.is_actively_holding_expected_zone.
            # This flag is true when:
            # 1. Mouse is down on the expected zone.
            # 2. Hold has been initiated correctly (not on cooldown, etc.).
            # 3. Mouse has not moved off the zone since initiation.
            # 4. Success for *this specific hold duration* has not yet occurred in this same frame
            #    (because `is_actively_holding_expected_zone` is reset upon success).
            # This seems correct for stat accrual *during* the act of a successful hold.
            
            # renpy.log(f"is_interacting returning: {self.is_actively_holding_expected_zone}") # Optional: for heavy debugging
            return self.is_actively_holding_expected_zone
        
        # rub_timer method is removed (ensure it's actually gone from the file)

        def update_puzzle_state(self):
            # Ensure global flags are accessible if update_stats or other functions here need to modify them
            # However, wrong_input_active etc. are modified by update_interaction_logic now.
            global wrong_input_active, wrong_input_start_time, penalty_active 

            self.update_interaction_logic() # New call to the main logic handler

            # The general mouse-up reset for wrong_input_active is removed.
            # wrong_input_active is now managed more specifically by update_interaction_logic
            # and by the consequences in update_stats.

            update_stats(self.is_interacting()) # Call update_stats with the current interaction state

        def reset(self):
            renpy.log(f"RubDebug: Puzzle {self.puzzle_number} RESET.")
            self.current_seq_index = 0
            # self.just_hit_zone = False # Removed
            self.cooldown_end_time = 0.0
            # self.last_rub_update_time = self.now_func() # Removed
            self.expected_zone = self.sequence[0] if self.sequence else None # Reset expected_zone
            self.current_active_zone = None

            self.current_hold_time_accumulated = 0.0
            self.is_actively_holding_expected_zone = False
            self.hold_start_time = 0.0
            self.hold_started_on_expected_zone = False

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
            
            # temp_factor must be calculated before this log, and exc_change_rate/trust_change_rate after.
            temp_factor = 1 + (jaily.temperature - 98.6) / (103.0 - 98.6) # Assuming 103 is a high temp benchmark
            temp_factor = max(0.5, min(temp_factor, 2.0)) # Clamp temp_factor to avoid extreme values

            # Calculate change rates before logging them
            exc_change_rate_val = adjustable_config.get("excitement_increase_rate",0.02) * jaily.trust * interaction_factor_for_stats * temp_factor - \
                                  adjustable_config.get("excitement_decay_rate",0.01) * jaily.excitement
            trust_change_rate_val = adjustable_config.get("trust_increase_rate",0.0075) * jaily.excitement * interaction_factor_for_stats * temp_factor - \
                                    adjustable_config.get("trust_decay_rate",0.005) * (jaily.trust - adjustable_config.get("trust_stat_baseline",50))

            if not wrong_input_active and interaction_factor_for_stats > 0 : # Log only when attempting to accrue positive stats
                log_interacting_flag = interacting_flag # From function argument
                log_jaily_trust = jaily.trust if 'jaily' in globals() and hasattr(jaily, 'trust') else -1
                log_jaily_excitement = jaily.excitement if 'jaily' in globals() and hasattr(jaily, 'excitement') else -1
                
                renpy.log(f"StatAccrual: Interacting={log_interacting_flag}, Trust={log_jaily_trust:.2f}, Excitement={log_jaily_excitement:.2f}, TempFactor={temp_factor:.2f}, ExcRateCfg={adjustable_config.get('excitement_increase_rate', -1)}, TrustRateCfg={adjustable_config.get('trust_increase_rate', -1)}, dExc_calc={exc_change_rate_val*dt:.4f}, dTrust_calc={trust_change_rate_val*dt:.4f}")

            if wrong_input_active : # and not penalty_active (i.e. during grace period of wrong input)
                 # If wrong input is active, even in its grace, positive stats shouldn't accrue.
                 # Setting interaction_factor to 0 or negative.
                 interaction_factor_for_stats = 0 # Or a negative value if decay is desired during wrong_input grace.

            # temp_factor = 1 + (jaily.temperature - 98.6) / (103.0 - 98.6) # Assuming 103 is a high temp benchmark # Moved up
            # temp_factor = max(0.5, min(temp_factor, 2.0)) # Clamp temp_factor to avoid extreme values # Moved up

            # Use the pre-calculated change rates
            jaily.excitement = min(100, max(0, jaily.excitement + exc_change_rate_val * dt))
            jaily.trust = min(100, max(0, jaily.trust + trust_change_rate_val * dt))

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

