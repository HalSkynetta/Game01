init python:
    # Store original functions that might be mocked by tests
    # This ensures they can be restored if needed, though for simple test labels,
    # this might be overkill if the game isn't run immediately after tests without a restart.
    if "_original_time_time" not in globals(): # Check if already defined
        _original_time_time = time.time
    if "_original_renpy_get_mouse_pos" not in globals():
        _original_renpy_get_mouse_pos = renpy.get_mouse_pos
    # Assuming left_mouse_down is the globally defined helper from 01_game_logic(Functional).rpy
    # We need to be careful if that file isn't loaded when this init python runs.
    # For simplicity, the Puzzle class now takes these as optional constructor args.
    if "Zone" not in globals(): # Ensure Zone is defined if not already imported (e.g. from game logic)
        from collections import namedtuple
        Zone = namedtuple("Zone", "x y width height")


label test_rubbing_mechanic():
    python:
        # --- Test Infrastructure ---
        _test_mock_now_time = 0.0
        _test_mock_mouse_pos_val = (0, 0)
        _test_mock_mouse_down_val = False

        # Minimal JailyState mock for Puzzle interaction (if Puzzle directly uses jaily)
        # The current Puzzle class doesn't directly use jaily, but get_hotzone_multiplier does.
        class MockJailyState:
            def __init__(self):
                self.excitement = 50 # For get_hotzone_multiplier

        _test_jaily_state = MockJailyState()

        # Minimal adjustable_config for tests
        # Values used by Puzzle constructor or rub_timer indirectly (e.g. get_hotzone_multiplier for cooldown)
        _test_adjustable_config = {
            "rub_distance_threshold": 25, # Updated to match game config
            "rub_time_limit": 0.75,       # Updated to match game config
            "cooldown_duration": 1.0,
            "excitement_stat_baseline": 50,     # For get_hotzone_multiplier
            "excitement_multiplier_at_min": 1.0, # Simplify hotzone to 1.0
            "excitement_multiplier_at_max": 1.0, # Simplify hotzone to 1.0
            # Add other keys if Puzzle's direct/indirect dependencies require them
        }

        _test_puzzle_zones_data = {
            "zone1": Zone(x=0, y=0, width=100, height=100),
            "zone2": Zone(x=100, y=100, width=100, height=100), # Example for T1's sequence
            # Define other zones if test scenarios use them by name for boundary checks
        }

        # Mock functions to be passed to Puzzle instance
        def get_mock_time():
            return _test_mock_now_time

        def get_mock_mouse_pos():
            return _test_mock_mouse_pos_val

        def get_mock_mouse_down():
            return _test_mock_mouse_down_val

        # Need to manage the global 'clicked_zoneX' variables that Puzzle.rub_timer reads
        # This is a bit of a hack due to globals but necessary for current Puzzle design.
        # We'll reset them for each scenario.
        _test_clicked_zones_state = {}
        for i in range(1, 15): # zone1-8, locked1-14 (overkill, but covers all)
            _test_clicked_zones_state[f"zone{i}"] = False
            _test_clicked_zones_state[f"locked{i}"] = False

        def set_clicked_zone(zone_name, is_clicked):
            global clicked_zone1, clicked_zone2, clicked_zone3, clicked_zone4, clicked_zone5, clicked_zone6, clicked_zone7, clicked_zone8
            global clicked_locked1, clicked_locked2, clicked_locked3, clicked_locked4, clicked_locked5, clicked_locked6, clicked_locked7, clicked_locked8, clicked_locked9, clicked_locked10, clicked_locked11, clicked_locked12, clicked_locked13, clicked_locked14

            # Reset all first
            for i in range(1, 9): globals()[f"clicked_zone{i}"] = False
            for i in range(1, 15): globals()[f"clicked_locked{i}"] = False

            if zone_name and is_clicked:
                if zone_name in globals():
                    globals()[zone_name] = True
                else:
                    renpy.log(f"Warning: Test tried to click unknown zone: {zone_name}")

        # Helper to run a scenario
        def run_test_scenario(scenario_name, steps, initial_sequence=None):
            global _test_mock_now_time, _test_mock_mouse_pos_val, _test_mock_mouse_down_val
            global wrong_input_active, wrong_input_start_time # Globals modified by Puzzle.rub_timer
            global jaily, adjustable_config # Globals used by Puzzle indirectly

            renpy.log(f"--- Starting Test Scenario: {scenario_name} ---")

            # Setup global context for the Puzzle instance
            jaily = _test_jaily_state
            adjustable_config = _test_adjustable_config # Make sure this is the global one Puzzle uses

            current_puzzle = Puzzle(puzzle_number=1, # Provide a puzzle_number for the constructor
                                    puzzle_zones_data=_test_puzzle_zones_data,
                                    now_func=get_mock_time,
                                    mouse_pos_func=get_mock_mouse_pos,
                                    mouse_down_func=get_mock_mouse_down)
            if initial_sequence:
                current_puzzle.sequence = initial_sequence # Allow custom sequence for testing

            # Reset persistent global state modified by rub_timer
            wrong_input_active = False
            wrong_input_start_time = None
            _test_mock_now_time = 0.0 # Reset time for each scenario

            for i, step in enumerate(steps):
                renpy.log(f"  Step {i+1}: {step.get('action_text', 'No action text')}")

                _test_mock_mouse_pos_val = step.get('mouse_pos', (0,0))
                _test_mock_mouse_down_val = step.get('mouse_down', False)
                set_clicked_zone(step.get('clicked_zone_name'), _test_mock_mouse_down_val)

                # Log state *before* rub_timer
                renpy.log(f"    Before rub_timer: time={_test_mock_now_time:.2f}, mouse_down={_test_mock_mouse_down_val}, active_zone={current_puzzle.current_active_zone}, rub_dist={current_puzzle.current_rub_distance:.2f}, rub_start_time={current_puzzle.current_rub_start_time:.2f}, initial_touch_spawned={current_puzzle.initial_touch_spawned}")

                current_puzzle.rub_timer()

                # Log state *after* rub_timer
                renpy.log(f"    After rub_timer: seq_idx={current_puzzle.current_seq_index}, wrong_input={wrong_input_active}, rub_dist={current_puzzle.current_rub_distance:.2f}, cooldown_end={current_puzzle.cooldown_end:.2f}, initial_touch_spawned={current_puzzle.initial_touch_spawned}")

                if 'expected_seq_index' in step:
                    assert current_puzzle.current_seq_index == step['expected_seq_index'], f"Expected seq_idx {step['expected_seq_index']}, got {current_puzzle.current_seq_index}"
                if 'expected_wrong_input' in step:
                    assert wrong_input_active == step['expected_wrong_input'], f"Expected wrong_input {step['expected_wrong_input']}, got {wrong_input_active}"
                if 'expected_rub_dist_reset_to_zero' in step and step['expected_rub_dist_reset_to_zero']:
                    assert abs(current_puzzle.current_rub_distance) < 0.001, f"Step {i+1} ({scenario_name}): Expected rub_dist near 0, got {current_puzzle.current_rub_distance:.2f}"
                if 'expected_cooldown_active' in step:
                    is_cooldown = current_puzzle.cooldown_end > _test_mock_now_time
                    assert is_cooldown == step['expected_cooldown_active'], f"Step {i+1} ({scenario_name}): Expected cooldown_active {step['expected_cooldown_active']}, got {is_cooldown}"
                if 'expected_initial_touch_spawned' in step:
                    assert current_puzzle.initial_touch_spawned == step['expected_initial_touch_spawned'], f"Step {i+1} ({scenario_name}): Expected initial_touch_spawned {step['expected_initial_touch_spawned']}, got {current_puzzle.initial_touch_spawned}"
                if 'expected_last_mouse_pos_none' in step and step['expected_last_mouse_pos_none']:
                    assert current_puzzle.last_mouse_pos is None, f"Step {i+1} ({scenario_name}): Expected last_mouse_pos to be None, got {current_puzzle.last_mouse_pos}"
                if 'expected_rub_start_time_zero' in step and step['expected_rub_start_time_zero']:
                    assert abs(current_puzzle.current_rub_start_time) < 0.001, f"Step {i+1} ({scenario_name}): Expected rub_start_time near 0, got {current_puzzle.current_rub_start_time:.2f}"


                _test_mock_now_time += step.get('advance_time', 0.1) # Advance time after assertions for the current step

            renpy.log(f"--- Finished Test Scenario: {scenario_name} ---\n")

        # --- Define Test Scenarios ---

        # T1: Successful Rub (distance accumulates over multiple frames)
        scenario_t1 = [
            {'action_text': "Press mouse in zone1 (10,10)", 'mouse_pos': (10,10), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.05, 'expected_seq_index': 0, 'expected_initial_touch_spawned': False}, # Rub starts, distance 0, start_time set
            {'action_text': "Move mouse in zone1 to (20,20) (feedback)", 'mouse_pos': (20,20), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.1, 'expected_seq_index': 0, 'expected_initial_touch_spawned': True}, # Dist ~14
            {'action_text': "Move mouse in zone1 to (30,30) (threshold met)", 'mouse_pos': (30,30), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.1, 'expected_seq_index': 1, 'expected_cooldown_active': True, 'expected_rub_dist_reset_to_zero': True, 'expected_initial_touch_spawned': False, 'expected_last_mouse_pos_none': True, 'expected_rub_start_time_zero': True}, # Dist ~14 + ~14 = ~28. Threshold 25. Total time = 0.05+0.1+0.1 = 0.25s < 0.75s. Success!
            {'action_text': "Mouse still down, in cooldown", 'mouse_pos': (30,30), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.5, 'expected_seq_index': 1, 'expected_cooldown_active': True, 'expected_initial_touch_spawned': False},
            {'action_text': "Release mouse", 'mouse_pos': (30,30), 'mouse_down': False, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.5, 'expected_seq_index': 1, 'expected_cooldown_active': True, 'expected_initial_touch_spawned': False},
            {'action_text': "Cooldown ends, press in zone2 (110,110)", 'mouse_pos': (110,110), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone2', 'advance_time': 0.1, 'expected_seq_index': 1, 'expected_cooldown_active': False, 'expected_initial_touch_spawned': False},
        ]
        run_test_scenario("T1: Successful Rub", scenario_t1, initial_sequence=["zone1", "zone2"])

        # T2: Rub Fails (Mouse Click-Leaves Zone - Ren'Py hotspot mechanism makes current_active_zone None)
        scenario_t2 = [
            {'action_text': "Press mouse in zone1 (10,10)", 'mouse_pos': (10,10), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.05, 'expected_seq_index': 0, 'expected_initial_touch_spawned': False},
            {'action_text': "Move mouse slightly in zone1 to (20,20)", 'mouse_pos': (20,20), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.1, 'expected_seq_index': 0, 'expected_initial_touch_spawned': True},
            {'action_text': "Mouse 'leaves' zone (clicked_zone_name is None)", 'mouse_pos': (200,200), 'mouse_down': True, 'clicked_zone_name': None, 'advance_time': 0.1, 'expected_seq_index': 0, 'expected_rub_dist_reset_to_zero': True, 'expected_initial_touch_spawned': False, 'expected_last_mouse_pos_none': True, 'expected_rub_start_time_zero': True},
            {'action_text': "Release mouse", 'mouse_pos': (200,200), 'mouse_down': False, 'clicked_zone_name': None, 'advance_time': 0.1, 'expected_seq_index': 0, 'expected_initial_touch_spawned': False},
        ]
        run_test_scenario("T2: Rub Fails (Mouse Click-Leaves Zone)", scenario_t2, initial_sequence=["zone1"])

        # T2b: Rub Interrupted (Mouse Physically Leaves Zone Boundary, sticky hotspot)
        scenario_t2b = [
            {'action_text': "Press mouse in zone1 (10,10)", 'mouse_pos': (10,10), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.05, 'expected_seq_index': 0, 'expected_initial_touch_spawned': False},
            {'action_text': "Move mouse slightly in zone1 to (20,20) (feedback)", 'mouse_pos': (20,20), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.1, 'expected_seq_index': 0, 'expected_initial_touch_spawned': True},
            {'action_text': "Move mouse physically OUTSIDE zone1 (to 150,150) but clicked_zone1 is 'sticky'", 'mouse_pos': (150,150), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.1, 'expected_seq_index': 0, 'expected_rub_dist_reset_to_zero': True, 'expected_initial_touch_spawned': False, 'expected_last_mouse_pos_none': True, 'expected_rub_start_time_zero': True},
            {'action_text': "Release mouse", 'mouse_pos': (150,150), 'mouse_down': False, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.1, 'expected_seq_index': 0, 'expected_initial_touch_spawned': False},
        ]
        run_test_scenario("T2b: Rub Interrupted (Mouse Physically Leaves Zone Boundary)", scenario_t2b, initial_sequence=["zone1"])

        # T3: Rub Fails (Total Time Limit Exceeded before Distance Met)
        scenario_t3 = [
            {'action_text': "Press mouse in zone1 (10,10)", 'mouse_pos': (10,10), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.05, 'expected_seq_index': 0, 'expected_initial_touch_spawned': False}, # Rub started, time = 0.05
            {'action_text': "Move mouse slightly to (15,15) (feedback)", 'mouse_pos': (15,15), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.1, 'expected_initial_touch_spawned': True}, # Rub dist ~7, time = 0.15
            {'action_text': "Hold, accumulate more time", 'mouse_pos': (15,15), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.5, 'expected_initial_touch_spawned': True}, # Rub dist ~7, time = 0.65. Still < 0.75
            {'action_text': "Time exceeds limit (0.65 + 0.15 = 0.80 > 0.75)", 'mouse_pos': (15,15), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.15, 'expected_seq_index': 0, 'expected_rub_dist_reset_to_zero': True, 'expected_initial_touch_spawned': False, 'expected_last_mouse_pos_none': True, 'expected_rub_start_time_zero': True},
        ]
        run_test_scenario("T3: Rub Fails (Total Time Limit Exceeded)", scenario_t3, initial_sequence=["zone1"])

        # T4: Rub Fails (Distance Not Met, Mouse Released Before Timeout)
        scenario_t4 = [
            {'action_text': "Press mouse in zone1 (10,10)", 'mouse_pos': (10,10), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.05, 'expected_initial_touch_spawned': False},
            {'action_text': "Move small distance to (15,15) (feedback)", 'mouse_pos': (15,15), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.1, 'expected_initial_touch_spawned': True}, # dist ~7
            {'action_text': "Move small distance again to (20,20)", 'mouse_pos': (20,20), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.1, 'expected_initial_touch_spawned': True}, # dist ~14. Total time 0.25s.
            {'action_text': "Release mouse (dist 14 < 25, time 0.25 < 0.75)", 'mouse_pos': (20,20), 'mouse_down': False, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.1, 'expected_seq_index': 0, 'expected_rub_dist_reset_to_zero': True, 'expected_initial_touch_spawned': False, 'expected_last_mouse_pos_none': True, 'expected_rub_start_time_zero': True},
        ]
        run_test_scenario("T4: Rub Fails (Distance Not Met, Mouse Released)", scenario_t4, initial_sequence=["zone1"])

        # T5: Interaction with Wrong Zone (mouse stays within wrong zone boundary)
        scenario_t5 = [
            {'action_text': "Press mouse in zone2 (110,110) (wrong zone)", 'mouse_pos': (110,110), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone2', 'advance_time': 0.05, 'expected_seq_index': 0, 'expected_wrong_input': True, 'expected_initial_touch_spawned': False},
            {'action_text': "Move mouse in zone2 to (130,130) (rubbing wrong zone, feedback)", 'mouse_pos': (130,130), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone2', 'advance_time': 0.1, 'expected_seq_index': 0, 'expected_wrong_input': True, 'expected_initial_touch_spawned': True, 'expected_rub_dist_reset_to_zero': True}, # Rub on wrong zone completes (dist ~28 > 25), resets dist, still wrong
            {'action_text': "Release mouse", 'mouse_pos': (130,130), 'mouse_down': False, 'clicked_zone_name': 'clicked_zone2', 'advance_time': 0.1, 'expected_seq_index': 0, 'expected_wrong_input': False, 'expected_initial_touch_spawned': False},
        ]
        run_test_scenario("T5: Interaction with Wrong Zone", scenario_t5, initial_sequence=["zone1", "zone2"])

        # T6: Click-Hold-No-Movement vs. Start-Movement (for is_interacting() and feedback in zone1)
        scenario_t6 = [
            {'action_text': "Press mouse in zone1 (10,10), no movement", 'mouse_pos': (10,10), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.1, 'expected_initial_touch_spawned': False, 'expected_seq_index': 0},
            {'action_text': "Hold in zone1 (10,10), still no movement", 'mouse_pos': (10,10), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.2, 'expected_initial_touch_spawned': False, 'expected_seq_index': 0},
            {'action_text': "Start moving slightly in zone1 to (12,12)", 'mouse_pos': (12,12), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.1, 'expected_initial_touch_spawned': True, 'expected_seq_index': 0},
            {'action_text': "Continue moving in zone1 to (30,30) to complete rub", 'mouse_pos': (30,30), 'mouse_down': True, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.1, 'expected_initial_touch_spawned': False, 'expected_seq_index': 1, 'expected_rub_dist_reset_to_zero': True, 'expected_cooldown_active': True, 'expected_last_mouse_pos_none': True, 'expected_rub_start_time_zero': True}, # total dist from (10,10) via (12,12) to (30,30) is >25
            {'action_text': "Release mouse", 'mouse_pos': (30,30), 'mouse_down': False, 'clicked_zone_name': 'clicked_zone1', 'advance_time': 0.1, 'expected_initial_touch_spawned': False, 'expected_seq_index': 1},
        ]
        run_test_scenario("T6: Click-Hold vs. Active Rubbing", scenario_t6, initial_sequence=["zone1"])

        # Restore original functions if they were patched (important if other game code runs after this label)
        # For a simple test label that just returns, this might not be strictly necessary.
        # time.time = _original_time_time
        # renpy.get_mouse_pos = _original_renpy_get_mouse_pos
        # left_mouse_down = _original_left_mouse_down # If it was globally patched

    $ renpy.log("Rubbing mechanic tests completed. Please check logs for details and assertions.")
    return
