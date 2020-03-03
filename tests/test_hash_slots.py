from rcc.hash_slot import getHashSlot


def test_hash_slots():
    assert getHashSlot('channel_2') == 1978
    assert getHashSlot('foo') == 12182

    # that's more of a speed test ...
    for i in range(100000):
        getHashSlot(str(i))
