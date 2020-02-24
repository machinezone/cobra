'''Binpacking algorithm

Adapted from https://pypi.org/project/binpacking/ to remove the numpy dependency

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import operator


def findIndexOfSmallestValue(values):
    idx, _ = min(enumerate(values), key=operator.itemgetter(1))
    return idx


def to_constant_bin_number(d, N_bin):
    '''
    Distributes a dictionary of weights
    to a fixed number of bins while trying to keep the weight distribution constant.
    INPUT:
    --- d: dictionary where each (key,value)-pair carries the weight as value,
    '''

    items = [(val, key) for key, val in d.items()]
    items.sort()
    items.reverse()
    weights = [item[0] for item in items]
    keys = [item[1] for item in items]

    bins = [{} for i in range(N_bin)]

    # the total volume is the sum of all weights
    V_total = sum(weights)

    # the first estimate of the maximum bin volume is
    # the total volume divided to all bins
    V_bin_max = V_total / float(N_bin)

    # prepare array containing the current weight of the bins
    weight_sum = [0.0 for _ in range(N_bin)]

    # iterate through the weight list, starting with heaviest
    for i, weight in enumerate(weights):

        key = keys[i]

        # put next value in bin with lowest weight sum
        b = findIndexOfSmallestValue(weight_sum)

        # calculate new weight of this bin
        new_weight_sum = weight_sum[b] + weight

        found_bin = False
        while not found_bin:

            # if this weight fits in the bin
            if new_weight_sum < V_bin_max:

                # ...put it in
                bins[b][key] = weight

                # increase weight sum of the bin and continue with
                # next item
                weight_sum[b] = new_weight_sum
                found_bin = True

            else:
                # if not, increase the max volume by the sum of
                # the rest of the bins per bin
                V_bin_max += sum(weights[i:]) / float(N_bin)

    return bins
