init python:
    # Global Player State
    class JailyState(object): # Added (object) for style, works fine without too in Py2/3
        def __init__(self):
            self.trust = 50
            self.excitement = 50
            self.hearts = 50
            self.temperature = 98.6
            self.embarrassment = 50
            self.game_over = False

    jaily = JailyState()

    # Adjustable Configuration
    adjustable_config = {
        "cooldown_duration": 1.0,
        "required_hold_time": 10.0, # As per monolithic script example
        "wrong_grace_period": 5.0,
        "wrong_transition_duration": 1.0,
        "penalty_excitement_rate": 0.05,
        "penalty_trust_rate": 0.05,
        "penalty_embarrassment_rate": 0.05,

        # EXCITEMENT STAT CONFIG
        "excitement_increase_rate": 0.02,
        "excitement_decay_rate": 0.01,
        "excitement_stat_baseline": 50,
        "excitement_multiplier_at_min": 0.5,
        "excitement_multiplier_at_max": 1.5,

        # TRUST STAT CONFIG
        "trust_increase_rate": 0.0075,
        "trust_decay_rate": 0.005,
        "trust_stat_baseline": 50,
        "trust_multiplier_at_min": 0.25,
        "trust_multiplier_at_max": 2.0,
        "trust_particle_phase_offset": 0.5,

        # HEARTS PARTICLE CONFIG
        "hearts_threshold": 25,
        "hearts_lower_bound": 30,
        "hearts_upper_bound": 100,
        "pps_at_lower_bound_hearts": 0.5,
        "pps_at_upper_bound_hearts": 10.0,

        # TRUST PARTICLE CONFIG (using specific keys as planned)
        "trust_particle_threshold": 31,
        "trust_particle_lower_bound": 51,
        "trust_particle_upper_bound": 100,
        "pps_at_lower_bound_trust_particle": 0.20,
        "pps_at_upper_bound_trust_particle": 0.5,

        # EXCITEMENT PARTICLE CONFIG (using specific keys as planned)
        "excitement_particle_threshold": 25,
        "excitement_particle_lower_bound": 30,
        "excitement_particle_upper_bound": 100,
        "pps_at_lower_bound_excitement_particle": 0.20,
        "pps_at_upper_bound_excitement_particle": 0.5,

        "particle_transition_duration": 5.0,
        "particle_update_interval": 0.016,

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

        # Heart shower adjustable attributes
        "heart_shower": {
            "duration": 3.0,
            "heart_count": 100,
            "x_start_min": -100,
            "x_start_max": 2020,
            "y_start_min": -200,
            "y_start_max": 0,
            "x_end_min": -100,
            "x_end_max": 2020,
            "y_end_min": 1180,
            "y_end_max": 2400,
            "rotation_min": -30,
            "rotation_max": 30,
            "scale_min": 0.75,
            "scale_max": 3.0
        },
        
        # Rub Grace Period Config (from previous 01_game_logic.rpy on GitHub)
        # These were likely intended for the more complex rub timer, but including for completeness of adjustable_config
        "rub_grace_period_min_trust": 1,
        "rub_grace_period_max_trust": 100,
        "rub_grace_period_min_duration": 0.5, 
        "rub_grace_period_max_duration": 2.0
    }

