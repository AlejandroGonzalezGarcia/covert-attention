from psychopy import visual, event, core
from .trials import Trial
from .parameters import build_config
from .utilities import display_message, save_results, save_to_project, define_mon, display_message_key_required

def run_experiment(stop_event=None, 
                   marker_queue=None, 
                   decode_active=None, 
                   decision_queue=None,
                   psychopy_params=None,
                   participant_id=None, 
                   run_dir=None,
                   results_queue=None,
                   offline_queue=None
                   ):
    
    print("Starting PsychoPy Experiment")

    # ---- import experiment parameters
    if psychopy_params is None:
        print("Using native psychopy parameters")
        params = build_config()
        participant_id = params.participant.participant_id
    else:
        print("Importing psychopy parameters")
        params = psychopy_params

    print(f"Participant: {participant_id}")
    print(params.monitor.units)
    # ---- define monitor
    mon = define_mon(params.monitor.resolution)

    #---- create window
    if params.monitor.fullscr == True:
        win = visual.Window(
            fullscr=True,
            monitor=mon,
            units=params.monitor.units,
            color="grey",
            waitBlanking=True
        )
    else:
        win = visual.Window(
            size=params.monitor.window_size,
            monitor=mon,
            units=params.monitor.units,
            color="grey",
            waitBlanking=True
        )

    # core.wait(0.5)

    #---- intro message
    intro_text = "Welcome!"
    display_message(win, intro_text)

    # # ---- create offline trials
    # offline_trials = Trial.create_offline_trials(
    #     params.ssvep.num_offline_trials,
    #     params.ssvep.offline_trial_duration,
    #     params.stimulus.stimuli_shapes,
    #     params.stimulus.stimuli_size,
    #     params.stimulus.stimuli_frequencies, 
    #     params.stimulus.stimuli_position,
    #     params.stimulus.stimuli_colours,
    #     params.monitor.refresh_rate, 
    #     win,
    #     attention="overt"
    # )

    # # ---- offline trials message
    # display_message_key_required(win,
    #                 "Press any key to begin the series of offline overt attention trials")

    # # ---- run offline covert trials
    # Trial.run_offline_trials(
    #     offline_trials,
    #     win,
    #     marker_queue=marker_queue,
    #     offline_queue=offline_queue,
    #     attention="overt"
    #     )
    
    # ---- create offline covert trials
    # offline_covert_trials = Trial.create_offline_trials(
    #     params.ssvep.num_offline_trials,
    #     params.ssvep.offline_trial_duration,
    #     params.stimulus.stimuli_shapes,
    #     params.stimulus.stimuli_size,
    #     params.stimulus.stimuli_frequencies, 
    #     params.stimulus.stimuli_position,
    #     params.stimulus.stimuli_colours,
    #     params.monitor.refresh_rate, 
    #     win,
    #     attention="covert"
    # )

    num_offline_trials = 1
    offline_trial_duration = 5.0
    shapes = ["square", "square"]
    sizes = [[2, 2], [2, 2]]

    freqs = [15, 10]
    colours = ["red", "green"]

    angles = [45, 135, 225, 315]  # left, right
    radial_distances = [2]

    refresh_hz = 60

    offline_covert_trials = Trial.create_offline_trials(
        params.ssvep.num_offline_trials,
        params.ssvep.offline_trial_duration,
        params.stimulus.stimuli_shapes,
        params.stimulus.stimuli_size,
        params.stimulus.stimuli_frequencies,
        params.stimulus.stimuli_colours,
        params.stimulus.stimuli_angles,
        params.stimulus.stimuli_distances,
        params.monitor.refresh_rate,
        win=win,
        attention="covert",
        shuffle=True)

    # ---- message for covert attention trials
    display_message_key_required(win,
                    "Press any key to begin the series of offline covert attention trials")
    
    # ---- display offline covert attention trials
    Trial.run_offline_trials(
        offline_covert_trials,
        win,
        marker_queue=marker_queue,
        offline_queue=offline_queue,
        attention="covert"
        )


    #---- end message
    end_text = "Thank you for completing the experiment. Bye!"
    display_message(win, end_text)

    # print(results)

    win.close()
    core.quit()

def main():
    run_experiment()

if __name__ == "__main__":
    main()