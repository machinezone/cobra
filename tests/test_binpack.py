'''Test bin packing

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

from rcc.binpack import to_constant_bin_number


def test_binpack():
    b = {'a': 10, 'b': 10, 'c': 11, 'd': 1, 'e': 2, 'f': 7}

    bins = to_constant_bin_number(b, 4)

    expected_results = [{'c': 11}, {'b': 10}, {'a': 10}, {'f': 7, 'e': 2, 'd': 1}]

    for expectedBin, Bin in zip(expected_results, bins):
        assert expectedBin == Bin
