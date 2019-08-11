from cobras.server.redis_subscriber import validatePosition


def test_position():
    assert validatePosition(None)
    assert validatePosition('$')
    assert validatePosition('0-0')
    assert validatePosition('12-12')
    assert not validatePosition('select foo from bar')
