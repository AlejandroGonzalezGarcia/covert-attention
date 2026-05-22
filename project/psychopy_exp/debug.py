
import random
import itertools

def create_offline_trials(num_offline_trials, offline_trial_duration, shapes, sizes, freqs, positions, colours, refresh_hz, win=None):
        """"
        creates list of offline trials which must be of fixed duration
        """
        # list of trials
        offline_trial_list = []

        print(f"number of trials: {num_offline_trials}")
        print(f"trial duration: {offline_trial_duration}")
        print(f"colours: {colours}")
        print(f"shapes: {shapes}")
        print(f"sizes: {sizes}")
        print(f"frequencies: {freqs}")
        print(f"positions: {positions}")

        num_targets = len(positions)
        num_conditions = len(colours) * len(freqs)
        total_trials = num_conditions * num_offline_trials
        print(f"conditions: {num_conditions}")
        print(f"trials per condition: {num_offline_trials}")
        print(f"trials: {total_trials}")
        print("Creating trials....")
        
        # all unique conditions
        conditions = []

        for freq_perm in itertools.permutations(freqs):
            condition = list(zip(colours, freq_perm))
            conditions.append(condition)
        # print(conditions)

        dummy_list = []
        for condition_idx, condition in enumerate(conditions):
              for rep in range(num_offline_trials):
                    for cue_colour in colours:
                        dummy_list.append({
                             "condition": condition,
                             "cue_colour": cue_colour
                        })

        # print(dummy_list)
        print("")
        for i, trial in enumerate(dummy_list):
            print(f"Trial {i+1}")
            cue = trial['cue_colour']
            targets = trial['condition']
            # print(targets)
            print(cue)
            for j, target in enumerate(targets):
                 colour, freq = target[0], target[1]
                 print(colour, freq, sizes[j], shapes[j])


                 
            # targets = []
            # print(trial)
            # for j, target in enumerate(trial):
            #     colour, freq = target[0], target[1]
            #     print(colour, freq, shapes[j], sizes[j])
            print("")
                    
                    
        

        return

create_offline_trials(1, 10, ["square","square"], [[2, 2],[2,2]], [15, 10], [[-7,0], [7,0]], ["red", "green"], 60)

