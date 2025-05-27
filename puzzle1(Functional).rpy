# This file contains Puzzle 1 specific elements,
# including its stage label and dedicated TouchScreen.

# Puzzle 1 specific TouchScreen
screen TouchScreen(): 
    # This is used for Puzzle1.
    zorder 100
    modal True
    vbox:
        xalign 0.5
        yalign 0.5
        spacing 20
        button:
            style "cyan_cooldown" # Defined in game_logic.rpy
            action NullAction()
            hovered SetVariable("clicked_cooldown", True) # clicked_cooldown is a global var from game_logic.rpy
            unhovered SetVariable("clicked_cooldown", False)
            text "Cooldown" xalign 0.5 yalign 0.5
        hbox:
            spacing 20
            button:
                style "red_hotzone" # Defined in game_logic.rpy
                action NullAction()
                hovered SetVariable("clicked_zone1", True) # clicked_zone1 is a global var from game_logic.rpy
                unhovered SetVariable("clicked_zone1", False)
                text "Zone1" xalign 0.5 yalign 0.5
            button:
                style "green_hotzone" # Defined in game_logic.rpy
                action NullAction()
                hovered SetVariable("clicked_zone2", True) # clicked_zone2 is a global var from game_logic.rpy
                unhovered SetVariable("clicked_zone2", False)
                text "Zone2" xalign 0.5 yalign 0.5
            button:
                style "blue_hotzone" # Defined in game_logic.rpy
                action NullAction()
                hovered SetVariable("clicked_locked1", True) # clicked_locked1 is a global var from game_logic.rpy
                unhovered SetVariable("clicked_locked1", False)
                text "Locked1" xalign 0.5 yalign 0.5

# Puzzle 1 Stage Label
label puzzle1_stage:
    $ puzzle_stage = 1
    # current_puzzle should be an instance of Puzzle class from game_logic.rpy
    # The Puzzle class in game_logic.rpy has the default sequence for Puzzle 1.
    $ current_puzzle = Puzzle() 
    $ reset_game()  # reset_game is from game_logic.rpy; it calls current_puzzle.reset()
    
    window hide
    # Show screens defined in game_logic.rpy or particle_system.rpy
    show screen sequence_display
    show screen TouchScreen # This is the Puzzle 1 specific TouchScreen defined above
    show screen ParticleManagerScreen 
    show screen particles_screen 
    show screen puzzle_stats_update
    show screen Primary_stats
    show screen game_state_check
    show screen overheat_overlay
    pause

