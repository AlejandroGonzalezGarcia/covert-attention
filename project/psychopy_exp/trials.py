import numpy as np
from .targets import Target
import random, itertools
from psychopy import visual, core, event 
from .utilities import display_message, send_marker, decode_flag, send_result, create_fixation, send_offline_metadata, get_side_from_position, generate_position_sets, polar_to_cartesian
from pylsl import local_clock

class Trial:
    def __init__(self, target_list, refresh_rate, duration, offline=False, attention=None, cue_colour=None):
        self.targets = target_list
        self.refresh_rate = refresh_rate
        self.duration = duration

        # flag for whether trial is an offline or an online trial
        self.offline = offline

        # self.target_to_look = None # target corresponding to position user is told to look at
        self.target_chosen = None
        self.direction_chosen = None
        self.target_to_look_at = None
        self.trial_correct = None
        self.direction = None
        
        self.fixation = None
        self.attention = attention
        self.cue_colour = cue_colour

        if attention is not None:
            if attention not in ["overt", "covert"]:
                raise ValueError("Attention parameter must be either overt or covert")
            self.attention = attention # overt/covert

        # handle case for one or more targets
        if len(self.targets) == 1:
            self.direction = "centre"

        if self.offline:
            print(f"Created offline trial cued colour: {self.cue_colour}")
        else:
            print(f"Created decoding trial with cued colour: {self.cue_colour}")
        
        print(f"number of targets in newly created trial: {len(self.targets)}")
        for target in self.targets:
            if self.cue_colour == target.colour:
                if target.position[0] < 0: 
                    self.direction = "left"
                elif target.position[0] > 0:
                    self.direction = "right"

        # calculate frames for trial
        self.total_frames = int(self.refresh_rate * self.duration)
        print(f"Frames in trial: {self.total_frames}")

        # def create_fixation(win, targets, direction_to_look, location=[0,0])
        # print(f"created trial with total frames: {self.total_frames}")

    def run_trial(self, min_time, win, trial_num, marker_queue=None, decode_active=None, decision_queue=None, results_queue=None):

        # send marker for trial start (includes text)
        if marker_queue:
            # win.callOnFlip(send_marker, marker_queue, "trial start", trial_num)
            send_marker(marker_queue, "trial start", trial_num) # send marker as soon as trial starts

        # direct participant where to look
        direction_message = f"Look at the target on the {self.direction} of the screen."
        display_message(win, direction_message)

        min_frames = int(self.refresh_rate * min_time) # no response possible before this frame is reached
        if decode_active:
            print(f"Will begin decoding after {min_time}s from stimulus onset")

        frameN = 0 # frame counter for iteration
        response = None # response
        rt = None # response time

        event.clearEvents() # clear events

        # fixation
        self.fixation = create_fixation(win, self.targets, self.direction)
        self.fixation.draw()
        win.flip()
        core.wait(1.0)

        # start clock and reset it before stimulus onset
        clock = core.Clock()
        clock.reset()

        result = {}

        decision = None
        decision_time = None
        onset_marker = False
        decode_started = False
        while frameN < self.total_frames:
            # exit condition
            keys = event.getKeys(
                keyList=['escape', 'q']
            )

            # draw fixation
            self.fixation.draw()

            # draw target 
            for target in self.targets:
                # print(f"Drawing {target.shape}")
                if target.is_on_this_frame(frameN, target.frames_per_cycle):
                    target.draw_target()
            # send marker for stimulus onset
            if not onset_marker and marker_queue:
                win.callOnFlip(
                    send_marker, 
                    marker_queue, "stimulus onset", trial_num
                    )
                onset_marker = True # make sure code above is only executed upon stimulus onset
                print(f"Stimulus onset at roughly {clock.getTime()}s into trial.")
            
            # open decoding only once response window is allowed
            if frameN == min_frames and not decode_started and decode_active is not None:
                win.callOnFlip(
                    decode_flag,
                    decode_active, "start"
                    )
                if marker_queue:
                    win.callOnFlip(
                        send_marker,
                        marker_queue, "decode start", trial_num
                    )
                print(f"Started decoding at roughly {clock.getTime()}s into trial.")
                decode_started = True
            
            if decode_started:
                # declare decision message
                if decision_queue is not None:
                    try:
                        decision = decision_queue.get_nowait() # receives selected frequency from decoding algorithm
                        print(f"Received decision: {decision['decision']} Hz")
                        decision_time = clock.getTime()
                    except:   
                        decision = None
            
            # update window
            win.flip()

            # escape condition
            for key in keys:
                if key == 'escape' or key == 'q':
                    win.close()
                    core.quit()
            
            # end trial if response is recorded
            if decision is not None:
                break
            
            # increment frame counter
            frameN += 1

        # stop decoding
        if decode_active is not None:
                decode_flag(decode_active, "stop")
        # send marker for end of trial
        if marker_queue:
            if decode_active is not None:
                send_marker(marker_queue,"decode end", trial_num)
            send_marker(marker_queue, "trial end", trial_num)

        # map decision to location and determine whether correct or not
        if decision is not None:
            for target in self.targets:
                if target.frequency == decision['decision']: # flickering frequency equals frequency selected by algorithm
                    # assign chosen target based on frequency
                    print(f"Target selected: {target.shape} at position: {target.position} ({target.direction}) flickering at: {target.frequency} Hz")
                    self.target_chosen = target
                    if self.target_chosen.position[0] > 0: # case where x coordinates of chosen are on the right half of screen
                        self.direction_chosen = "right"
                    else: # case where x coordinates of chosen target are on left hand of the screen
                        self.direction_chosen = "left"
                # if target direction is equal to direction told to look at in the trial
                if target.direction == self.direction:
                    self.target_to_look_at = target
                    print(f"Target to look at: {target.shape} at position: {target.position} ({target.direction}) flickering at: {target.frequency} Hz")

        self.trial_correct = True if self.direction == self.direction_chosen else False

        print(f"Trial correct: {self.trial_correct}")

        print(f"Trial duration: {clock.getTime()}")
        print(f"Number of frames in trial: {frameN}")
        # even on trials with no input, create a result at the end of the trial
        result["response"] = self.direction_chosen
        result["time_of_response"] = decision_time
        result["direction_to_look"] = self.direction
        for i, target in enumerate(self.targets):
            result[f"{target.shape}"] = {
                "position": target.position,
                "frequency": target.frequency
            }

        if results_queue is not None:
            result_to_send = {}
            result_to_send["trial"] = trial_num
            result_to_send["target_direction"] = self.direction
            result_to_send["target_frequency"] = self.target_to_look_at.frequency
            result_to_send["response"] = self.direction_chosen
            result_to_send["response_frequency"] = self.target_chosen.frequency
            result_to_send["rt"] = decision_time
            result_to_send["correct"] = self.trial_correct
            send_result(results_queue, result_to_send)

        # print(f"trial results: {result}")

        display_message(win, f"Your decision: {self.direction_chosen}\nTold to look at: {self.direction}")
        win.flip()

        return result 

    def run_offline_trial(self, trial_num, win, marker_queue=None, offline_queue=None, attention=None):
        # send marker for trial start (includes text)
        if marker_queue:
            # win.callOnFlip(send_marker, marker_queue, "trial start", trial_num)
            send_marker(marker_queue, "trial start", trial_num, "offline") # send marker as soon as trial starts

        # direct participant where to look
        if attention == "covert":
            direction_message = f"Look at the target in the centre of the screen, but pay \
attention to the target on the {self.direction} of the screen"
        else:
            direction_message = f"Look at the target on the {self.direction} of the screen."
        display_message(win, direction_message)

        frameN = 0 # frame counter for iteration
        response = None # response
        rt = None # response time

        event.clearEvents() # clear events

        # fixation
        self.fixation = create_fixation(win, self.targets, self.direction, attention=attention)
        self.fixation.draw()
        win.flip()
        core.wait(1.0)

        # start clock and reset it before stimulus onset
        clock = core.Clock()
        clock.reset()

        decision = None
        onset_marker = False
        while frameN < self.total_frames:
            # exit condition
            keys = event.getKeys(
                keyList=['escape', 'q']
            )

            # draw fixation
            self.fixation.draw()

            # draw target 
            for target in self.targets:
                # print(f"Drawing {target.shape}")
                if target.is_on_this_frame(frameN, target.frames_per_cycle):
                    target.draw_target()
            # send marker for stimulus onset
            if not onset_marker and marker_queue:
                win.callOnFlip(
                    send_marker, 
                    marker_queue, "stimulus onset", trial_num
                    )
                onset_marker = True # make sure code above is only executed upon stimulus onset
                print(f"Stimulus onset at roughly {clock.getTime()}s into trial.")
            
            # update window
            win.flip()

            # escape condition
            for key in keys:
                if key == 'escape' or key == 'q':
                    win.close()
                    core.quit()
            
            # increment frame counter
            frameN += 1

        print(f"Trial duration: {clock.getTime()}")

        # metadata
        metadata = {}
        metadata['trial'] = trial_num
        metadata['attention_mode'] = attention # overt/covert
        for target in self.targets:
            if target.colour == self.cue_colour:
                metadata['target_colour'] = target.colour
                metadata['target_frequency'] = target.freq
                metadata['target_side'] = target.direction
            if target.direction == "left":
                metadata['left_colour'] = target.colour
                metadata['left_frequency'] = target.freq
            elif target.direction == "right":
                metadata['right_colour'] = target.colour
                metadata['right_frequency'] = target.freq
                

        if marker_queue:
            send_marker(marker_queue, "trial end", trial_num, "offline")
        if offline_queue:
            send_offline_metadata(offline_queue, metadata)
        
        win.flip()


    @staticmethod
    def create_trials(num_trials, trial_duration, shapes, sizes, freqs, positions, colours, refresh_hz, win):
        """
        creates list of trials

        parameters
        ----
        num_trials: int
            number of trials to create
        """
        # initialize trial list
        trial_list = []
        freqs = freqs.copy()
        colours = colours.copy()
        # random.shuffle(colours)
        random.shuffle(freqs)
        for _ in range(num_trials):
            # generate random cued colour
            cue_colour = random.choice(colours)
            # initialize target list
            targets = []
            # create targets according to parameters
            for i, shape in enumerate(shapes):
                targets.append(Target(shape, sizes[i], colours[i], freqs[i], refresh_hz, win))
            # append trial to trial list
            trial_list.append(Trial(targets, positions, refresh_hz, trial_duration, cue_colour=cue_colour))
        return trial_list
    
    # self, target_list, locations, refresh_rate, duration, offline=False, attention=None, cue_colour=None
    
    @staticmethod
    def create_offline_trials(
    num_offline_trials,
    offline_trial_duration,
    shapes,
    sizes,
    freqs,
    colours,
    angles,
    radial_distances,
    refresh_hz,
    win=None,
    attention=None,
    shuffle=True
    ):
        """
        Creates offline trials where:
        - positions are generated from angles and radial distances
        - all stimuli on the left side share one colour/frequency
        - all stimuli on the right side share one colour/frequency
        - left/right colour assignment is counterbalanced
        - left/right frequency assignment is counterbalanced
        - cue colour is varied
        """

        offline_trial_list = []

        sides = ["left", "right"]
        side_to_idx = {
            "left": 0,
            "right": 1
        }

        if len(shapes) != 2:
            raise ValueError("shapes should have length 2: [left_shape, right_shape].")

        if len(sizes) != 2:
            raise ValueError("sizes should have length 2: [left_size, right_size].")

        if len(colours) != 2:
            raise ValueError("colours should have length 2: one colour per side.")

        if len(freqs) != 2:
            raise ValueError("freqs should have length 2: one frequency per side.")

        position_sets = generate_position_sets(angles, radial_distances)

        for position_info in position_sets:
            radius = position_info["radius"]
            positions = position_info["positions"]
            angles_for_set = position_info["angles"]

            for colour_perm in itertools.permutations(colours):
                for freq_perm in itertools.permutations(freqs):

                    side_assignment = {}

                    for side_idx, side in enumerate(sides):
                        side_assignment[side] = {
                            "colour": colour_perm[side_idx],
                            "frequency": freq_perm[side_idx],
                            "shape": shapes[side_idx],
                            "size": sizes[side_idx]
                        }

                    condition = []

                    for stim_idx, position in enumerate(positions):
                        side = get_side_from_position(position)
                        side_idx = side_to_idx[side]

                        target_info = {
                            "stim_idx": stim_idx,
                            "side": side,
                            "position": position,
                            "angle": angles_for_set[stim_idx],
                            "radius": radius,

                            # inherited from side-level assignment
                            "colour": side_assignment[side]["colour"],
                            "frequency": side_assignment[side]["frequency"],
                            "shape": shapes[side_idx],
                            "size": sizes[side_idx]
                        }

                        condition.append(target_info)

                    for rep in range(num_offline_trials):
                        for cue_colour in colours:
                            trial = {
                                "condition": condition,
                                "side_assignment": side_assignment,
                                "cue_colour": cue_colour,
                                "rep": rep,
                                "duration": offline_trial_duration,
                                "refresh_hz": refresh_hz
                            }

                            offline_trial_list.append(trial)

        if shuffle:
            random.shuffle(offline_trial_list)

        print(f"Total number of trials: {len(offline_trial_list)}")
        final_list = []
        for trial in offline_trial_list:
            cue_colour=trial['cue_colour']
            target_list = []
            for target in trial['condition']:
                target_list.append(Target(
                    shape=target['shape'],
                    size=target['size'],
                    colour=target['colour'],
                    freq=target['frequency'],
                    refresh_hz=refresh_hz,
                    win=win,
                    position=target['position']
                ))
            final_list.append(Trial(
                target_list=target_list,
                refresh_rate=refresh_hz,
                duration=offline_trial_duration,
                offline=True,
                attention="covert",
                cue_colour=trial['cue_colour']
            ))

        print(f"Total trials: {len(final_list)}")
        # return offline_trial_list
        return final_list


    @staticmethod
    def run_all_trials(trial_list, min_trial_duration, win, marker_queue=None, decode_active=None, trial_pause=3.0, decision_queue=None, results_queue=None):
        """
        iterates over list of trials and displays them

        params
        ----
        trial_list: List[Trial]
            list of trials to display
        min_trial_duration: int
            minimum duration of trial before a response is allowed
        win: visual.Window:
            psychopy window
        trial_pause: float
            time between trials
        """
        # initialize results dictionary
        trial_results = {}

        # -----main trial loop
        for i, trial in enumerate(trial_list):
            trial_num = i + 1
            # trial intro
            print(f"==== Starting trial {trial_num} ====\n")
            trial.describe_trial()

            # run trial and save it to results dictionary
            trial_results[f"Trial {trial_num}"] = trial.run_trial(min_trial_duration, win, trial_num, marker_queue, decode_active, decision_queue, results_queue)

            # end of trial
            print(f"\n==== End of trial {trial_num} ====")

            core.wait(trial_pause)

            if i < len(trial_list)-1:
                print("")
        return trial_results
    
    # def run_offline_trial(self, trial_num, win, marker_queue=None, offline_queue=None):
    @staticmethod
    def run_offline_trials(trial_list, win, marker_queue=None, offline_queue=None, trial_pause=3.0, attention=None):
        """
        Iterates over offline trials and displays them
        """
        for i, trial in enumerate(trial_list):
            trial_num = i + 1
            print(f"==== Starting offline trial {trial_num}: ====\n")
            trial.describe_trial()

            trial.run_offline_trial(trial_num, win, marker_queue=marker_queue, offline_queue=offline_queue, attention=attention)

            # end of trial
            print(f"\n==== End of offline trial {trial_num} ====\n")

            core.wait(trial_pause)

        if i < len(trial_list)-1:
                print("")

    def describe_trial(self):
        description = ""
        description += f"Trial type: {self.attention}\n\
Queued colour: {self.cue_colour}\n\
Trial duration: {self.duration}\n"
        for i, target in enumerate(self.targets):
            description += f"Shape {i+1}: {target.shape}\n\
colour: {target.colour}\n\
frequency: {target.freq}\n\
position: {target.position}\n\
frames per cycle: {target.frames_per_cycle}"
            if i < len(self.targets)-1:
                description += "\n"
        description += "\n"

        print(description)
