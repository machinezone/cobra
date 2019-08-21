'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

from cobras.server.stream_sql import match_stream_sql_filter


def test_answer():
    miso_sql_filter = "SELECT * from blah WHERE device.game = 'miso'"
    miso_msg = {'device': {'game': 'miso'}}
    ody_msg = {'device': {'game': 'ody'}}

    assert match_stream_sql_filter(miso_sql_filter, miso_msg)
    assert not match_stream_sql_filter(miso_sql_filter, ody_msg)


def test_invalid_sql():
    sql_filter = "select *"
    msg = {'device': {'game': 'miso'}}

    assert not match_stream_sql_filter(sql_filter, msg)


def test_answer_bad_message_list():
    sql_filter = "select * from blah where device.game = 'miso'"
    msg = []

    assert not match_stream_sql_filter(sql_filter, msg)


def test_answer_bad_message_list_of_list():
    sql_filter = "select * from blah where device.game = 'miso'"
    msg = [[]]

    assert not match_stream_sql_filter(sql_filter, msg)


def test_answer_bad_message_string():
    sql_filter = "select * from blah where device.game = 'miso'"
    msg = 'asdcasdcadcascd'

    assert not match_stream_sql_filter(sql_filter, msg)


def test_answer_bad_message_none():
    sql_filter = "select * from blah where device.game = 'miso'"
    msg = None

    assert not match_stream_sql_filter(sql_filter, msg)


def test_answer_bad_message_list():
    sql_filter = "select * from blah"
    msg = {}

    assert match_stream_sql_filter(sql_filter, msg) == {}


def test_filter_is_none():
    sql_filter = None
    msg = []

    assert not match_stream_sql_filter(sql_filter, msg)


def test_check_filter_sms_id():
    sql_filter = "select * from blah where id = 'sms_test_id'"
    msg_pass = {'id': 'sms_test_id'}
    msg_fail = {'id': 'bar'}

    assert match_stream_sql_filter(sql_filter, msg_pass)
    assert not match_stream_sql_filter(sql_filter, msg_fail)


def test_check_filter_nested():
    sql_filter = "select * from blah where foo.bar.baz = '10'"
    msg_pass = {'foo': {'bar': {'baz': '10'}}}
    msg_fail = {'id': 'bar'}

    assert match_stream_sql_filter(sql_filter, msg_pass)
    assert not match_stream_sql_filter(sql_filter, msg_fail)


# FIXME: ints are unsupported
def _test_check_filter_int():
    sql_filter = "select * from blah where baz = 10"
    msg_pass = {'baz': 10}
    msg_fail = {'baz': 11}

    assert match_stream_sql_filter(sql_filter, msg_pass)
    assert not match_stream_sql_filter(sql_filter, msg_fail)


def test_check_and_combination():
    sql_filter = "select * from blah where game = 'ody' AND os_name = 'Android'"
    msg_pass = {'game': 'ody', 'os_name': 'Android'}
    msg_fail = {'game': 'ody', 'os_name': 'iOS'}

    assert match_stream_sql_filter(sql_filter, msg_pass)
    assert not match_stream_sql_filter(sql_filter, msg_fail)


def test_check_or_combination():
    sql_filter = "select * from blah where game = 'ody' OR os_name = 'Android'"
    msg_pass = {'game': 'niso', 'os_name': 'Android'}
    msg_fail = {'game': 'ody', 'os_name': 'iOS'}

    assert match_stream_sql_filter(sql_filter, msg_pass)
    assert match_stream_sql_filter(sql_filter, msg_fail)


def test_like_statement():
    miso_sql_filter = "SELECT * from blah WHERE device.game LIKE 'iso'"
    miso_msg = {'device': {'game': 'miso'}}
    ody_msg = {'device': {'game': 'ody'}}

    assert match_stream_sql_filter(miso_sql_filter, miso_msg)
    assert not match_stream_sql_filter(miso_sql_filter, ody_msg)


def test_booleans_true():
    essential_sql_filter = "SELECT * from blah WHERE data.essential = true"
    essential_msg = {'data': {'essential': True}}
    non_essential_msg = {'data': {'essential': False}}

    assert match_stream_sql_filter(essential_sql_filter, essential_msg)
    assert not match_stream_sql_filter(essential_sql_filter, non_essential_msg)


def test_booleans_false():
    essential_sql_filter = "SELECT * from blah WHERE data.essential = false"
    essential_msg = {'data': {'essential': True}}
    non_essential_msg = {'data': {'essential': False}}

    assert not match_stream_sql_filter(essential_sql_filter, essential_msg)
    assert match_stream_sql_filter(essential_sql_filter, non_essential_msg)


def test_int_equal():
    sql_filter = "SELECT * from blah WHERE data.file_count = 10"
    low_file_count_msg = {'data': {'file_count': 10}}
    high_file_count_msg = {'data': {'file_count': 100}}

    assert match_stream_sql_filter(sql_filter, low_file_count_msg)
    assert not match_stream_sql_filter(sql_filter, high_file_count_msg)


def test_int_multiple_conditions():
    sql_filter = """SELECT * from `blah` WHERE data.file_count = 16
                                         AND data.payload_KB = 5637
                                         AND data.essential = true
                 """
    hit = {
        'data': {
            'bundled_assets_check': '6988e3449c7ec3f4',
            'essential': True,
            'failed_patches_count': 0,
            'file_count': 16,
            'manifest_bundled_assets_check': '6988e3449c7ec3f4',
            'patches_applicable': True,
            'payload_KB': 5637,
            'runtime_second': 15.72719062300166,
            'storage_empty': True,
        }
    }
    miss = {'data': {'file_count': 100}}

    assert match_stream_sql_filter(sql_filter, hit)
    assert not match_stream_sql_filter(sql_filter, miss)


def test_different_operand():
    sql_filter = """SELECT * from `blah` WHERE data.file_count != 16
                                         AND data.essential != true
                                         AND data.description != 'content_sync'
                 """
    hit = {
        'data': {
            'essential': False,
            'file_count': 17,
            'description': 'content_sync_oops',
        }
    }
    miss = {
        'data': {'essential': True, 'file_count': 15, 'description': 'content_sync'}
    }

    assert match_stream_sql_filter(sql_filter, hit)
    assert not match_stream_sql_filter(sql_filter, miss)


def test_larger_than_operand():
    sql_filter = """SELECT * from `blah` WHERE data.file_count > 16
                 """
    hit = {'data': {'file_count': 17}}
    miss = {'data': {'file_count': 15}}

    assert match_stream_sql_filter(sql_filter, hit)
    assert not match_stream_sql_filter(sql_filter, miss)


def test_select_with_subfields_1():
    sql_filter = """SELECT device.app_version from `blah`
                 """
    hit = {'data': {'file_count': 17}, 'device': {'app_version': '4.3.2'}}
    miss = {'data': {'file_count': 15}}

    assert {"device.app_version": "4.3.2"} == match_stream_sql_filter(sql_filter, hit)


def test_select_with_subfields_2():
    sql_filter = """SELECT device.app_version from `blah` WHERE data.file_count > 16
                 """
    hit = {'data': {'file_count': 17}, 'device': {'app_version': '4.3.2'}}
    miss = {'data': {'file_count': 15}}

    assert {"device.app_version": "4.3.2"} == match_stream_sql_filter(sql_filter, hit)
    assert not match_stream_sql_filter(sql_filter, miss)


def test_select_with_multiple_subfields():
    sql_filter = """SELECT device.app_version,data.file_count from `blah` WHERE data.file_count > 16
                 """
    hit = {'data': {'file_count': 17}, 'device': {'app_version': '4.3.2'}}
    miss = {'data': {'file_count': 15}}

    assert {
        "device.app_version": "4.3.2",
        'data.file_count': 17,
    } == match_stream_sql_filter(sql_filter, hit)
    assert not match_stream_sql_filter(sql_filter, miss)
