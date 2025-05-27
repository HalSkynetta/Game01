label start:
    show screen Primary_stats
    "This is a story placeholder before the first puzzle."
    show screen overheat_overlay
    jump puzzle1_stage

label story2:
    window show
    show screen Primary_stats
    "This is a story placeholder before the second puzzle."
    jump puzzle2_stage

label story3:
    window show
    show screen Primary_stats
    "This is a story placeholder before the third puzzle."
    jump puzzle3_stage

label story4:
    window show
    show screen Primary_stats
    "This is a story placeholder before the fourth puzzle."
    jump puzzle4_stage

label story5:
    window show
    show screen Primary_stats
    "This is a story placeholder before the fifth puzzle."
    jump puzzle5_stage

label story6:
    window show
    show screen Primary_stats
    "This is a story placeholder for the final part of the game."

label game_over_max_temp:
    call hide_all_ui
    "Game Over: Temperature too high!"
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
    "Game Over: Temperature too low!"
    return

label outcome_puzzle:
    hide screen TouchScreen
    hide screen TouchScreen2
    hide screen TouchScreen3
    hide screen TouchScreen4
    hide screen TouchScreen5
    hide screen ParticleManagerScreen
    hide screen particles_screen
    hide screen puzzle_stats_update
    hide screen Primary_stats
    hide screen game_state_check
    hide screen sequence_display
    hide screen overheat_overlay
    "Congratulations! Puzzle completed successfully!"
    $ next_story = "story{}".format(puzzle_stage + 1)
    jump expression next_story

