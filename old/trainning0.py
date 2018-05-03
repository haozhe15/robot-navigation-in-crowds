from GameClass import GameClass
import numpy as np
import random
import csv
from nn import neural_net, LossHistory
import os.path
import timeit


TUNING = False
GAMMA = 0.9
NUM_INPUT = 10
fps = 40
def train(model, params):
    EPSILON = 0.5
    batchSize = params['batchSize']
    buffer = params['buffer']
    epochs = 10
    MAX_ACTIONS = 300

    for i in range(epochs):

        # Create a new game instance.
        game_object = GameClass(False,fps)

        # Get initial state by doing nothing and getting the state.
        reward, state = game_object.frame_step((2))

        # while game still in progress
        status = 1

        # count number of frames
        num_actions = 0

        while (status == 1):
            # We are in state S
            # Let's run our Q function on S to get Q values for all possible actions
            qval = model.predict(state.reshape(1, NUM_INPUT), batch_size=batchSize)
            if (random.random() < EPSILON):  # choose random action
                action = np.random.randint(0, 3)
            else:  # choose best action from Q(s,a) values
                action = (np.argmax(qval))
            # Change the action on every fps step, observe new state and reward
            for j in range(fps):
                if j == 0:
                    game_object.frame_step(action)
                elif j < fps-1:
                    game_object.frame_step(2)
                else:
                    reward, new_state = game_object.frame_step(2)
            num_actions+=1
            print('Epoch %d: num_frames:%d' % (i,num_actions))
            # Get max_Q(S',a)
            newQ = model.predict(new_state.reshape(1, NUM_INPUT), batch_size=batchSize)
            maxQ = np.max(newQ)
            y = np.zeros((1, 3))
            y[:] = qval[:]
            if reward < 9000:  # non-terminal state
                update = (reward + (GAMMA * maxQ))
            else:  # terminal state
                update = reward
            y[0][action] = update  # target output
            # print("Game #: %s" % (i,))
            model.fit(
                state.reshape(1,NUM_INPUT), y, batch_size=batchSize,
                epochs=1, verbose=0
            )
            state = new_state

            if reward > 9000 or num_actions >= MAX_ACTIONS:
                status = 0

            if EPSILON > 0.1:
                EPSILON -= (1 / MAX_ACTIONS)
    model.save_weights('saved-models/nn_model_3.h5',overwrite=True)
    return model

if __name__ == "__main__":
    if TUNING:
        param_list = []
        nn_params = [[164, 150], [256, 256],
                     [512, 512], [1000, 1000]]
        batchSizes = [40, 100, 400]
        buffers = [10000, 50000]

        for nn_param in nn_params:
            for batchSize in batchSizes:
                for buffer in buffers:
                    params = {
                        "batchSize": batchSize,
                        "buffer": buffer,
                        "nn": nn_param
                    }
                    param_list.append(params)

        for param_set in param_list:
            model = neural_net(NUM_INPUT, param_set['nn'])
            train(model, param_set)

    else:
        nn_param = [256, 256]
        params = {
            "batchSize": 40,
            "buffer": 10000,
            "nn": nn_param
        }
        model = neural_net(NUM_INPUT, nn_param)
        model = train(model, params)