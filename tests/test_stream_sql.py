'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

from cobras.server.stream_sql import match_stream_sql_filter


def test_answer():
    miso_sql_filter = "SELECT * FROM blah WHERE device.game = 'miso'"
    miso_msg = {'device': {'game': 'miso'}}
    ody_msg = {'device': {'game': 'ody'}}

    assert match_stream_sql_filter(miso_sql_filter, miso_msg)
    assert not match_stream_sql_filter(miso_sql_filter, ody_msg)


def test_invalid_sql():
    sql_filter = "SELECT *"
    msg = {'device': {'game': 'miso'}}

    assert not match_stream_sql_filter(sql_filter, msg)


def test_answer_bad_message_list():
    sql_filter = "SELECT * FROM blah WHERE device.game = 'miso'"
    msg = []

    assert not match_stream_sql_filter(sql_filter, msg)


def test_answer_bad_message_list_of_list():
    sql_filter = "SELECT * FROM blah WHERE device.game = 'miso'"
    msg = [[]]

    assert not match_stream_sql_filter(sql_filter, msg)


def test_answer_bad_message_string():
    sql_filter = "SELECT * FROM blah WHERE device.game = 'miso'"
    msg = 'asdcasdcadcascd'

    assert not match_stream_sql_filter(sql_filter, msg)


def test_answer_bad_message_none():
    sql_filter = "SELECT * FROM blah WHERE device.game = 'miso'"
    msg = None

    assert not match_stream_sql_filter(sql_filter, msg)


def test_answer_bad_message_dictionary():
    sql_filter = "SELECT * FROM blah"
    msg = {}

    assert match_stream_sql_filter(sql_filter, msg) == {}


def test_filter_is_none():
    sql_filter = None
    msg = []

    assert not match_stream_sql_filter(sql_filter, msg)


def test_check_filter_sms_id():
    sql_filter = "SELECT * FROM blah WHERE id = 'sms_test_id'"
    msg_pass = {'id': 'sms_test_id'}
    msg_fail = {'id': 'bar'}

    assert match_stream_sql_filter(sql_filter, msg_pass)
    assert not match_stream_sql_filter(sql_filter, msg_fail)


def test_check_filter_nested():
    sql_filter = "SELECT * FROM blah WHERE foo.bar.baz = '10'"
    msg_pass = {'foo': {'bar': {'baz': '10'}}}
    msg_fail = {'id': 'bar'}

    assert match_stream_sql_filter(sql_filter, msg_pass)
    assert not match_stream_sql_filter(sql_filter, msg_fail)


# FIXME: ints are unsupported
def _test_check_filter_int():
    sql_filter = "SELECT * FROM blah WHERE baz = 10"
    msg_pass = {'baz': 10}
    msg_fail = {'baz': 11}

    assert match_stream_sql_filter(sql_filter, msg_pass)
    assert not match_stream_sql_filter(sql_filter, msg_fail)


def test_check_and_combination():
    sql_filter = "SELECT * FROM blah WHERE game = 'ody' AND os_name = 'Android'"
    msg_pass = {'game': 'ody', 'os_name': 'Android'}
    msg_fail = {'game': 'ody', 'os_name': 'iOS'}

    assert match_stream_sql_filter(sql_filter, msg_pass)
    assert not match_stream_sql_filter(sql_filter, msg_fail)


def test_check_or_combination():
    sql_filter = "SELECT * FROM blah WHERE game = 'ody' OR os_name = 'Android'"
    msg_pass = {'game': 'niso', 'os_name': 'Android'}
    msg_fail = {'game': 'ody', 'os_name': 'iOS'}

    assert match_stream_sql_filter(sql_filter, msg_pass)
    assert match_stream_sql_filter(sql_filter, msg_fail)


def test_like_statement():
    miso_sql_filter = "SELECT * FROM blah WHERE device.game LIKE '_iso'"
    miso_msg = {'device': {'game': 'miso'}}
    ody_msg = {'device': {'game': 'ody'}}

    assert match_stream_sql_filter(miso_sql_filter, miso_msg)
    assert not match_stream_sql_filter(miso_sql_filter, ody_msg)


def test_like_statement2():
    miso_sql_filter = "SELECT * FROM blah WHERE device.game LIKE '*iso'"
    miso_msg = {'device': {'game': 'werwerweriso'}}
    ody_msg = {'device': {'game': 'ody'}}

    assert match_stream_sql_filter(miso_sql_filter, miso_msg)
    assert not match_stream_sql_filter(miso_sql_filter, ody_msg)


def test_like_statement3():
    miso_sql_filter = "SELECT * FROM blah WHERE session LIKE '*aa'"
    good_session = {'session': 'asdcasdcasdcadscaa'}
    bad_session = {'session': 'asdcasdcasdcadcasbb'}

    assert match_stream_sql_filter(miso_sql_filter, good_session)
    assert not match_stream_sql_filter(miso_sql_filter, bad_session)


def test_booleans_true():
    essential_sql_filter = "SELECT * FROM blah WHERE data.essential = true"
    essential_msg = {'data': {'essential': True}}
    non_essential_msg = {'data': {'essential': False}}

    assert match_stream_sql_filter(essential_sql_filter, essential_msg)
    assert not match_stream_sql_filter(essential_sql_filter, non_essential_msg)


def test_booleans_false():
    essential_sql_filter = "SELECT * FROM blah WHERE data.essential = false"
    essential_msg = {'data': {'essential': True}}
    non_essential_msg = {'data': {'essential': False}}

    assert not match_stream_sql_filter(essential_sql_filter, essential_msg)
    assert match_stream_sql_filter(essential_sql_filter, non_essential_msg)


def test_int_equal():
    sql_filter = "SELECT * FROM blah WHERE data.file_count = 10"
    low_file_count_msg = {'data': {'file_count': 10}}
    high_file_count_msg = {'data': {'file_count': 100}}

    assert match_stream_sql_filter(sql_filter, low_file_count_msg)
    assert not match_stream_sql_filter(sql_filter, high_file_count_msg)


def test_int_multiple_conditions():
    sql_filter = """SELECT * FROM `blah` WHERE data.file_count = 16
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
    sql_filter = """SELECT * FROM `blah` WHERE data.file_count != 16
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
    sql_filter = """SELECT * FROM `blah` WHERE data.file_count > 16
                 """
    hit = {'data': {'file_count': 17}}
    miss = {'data': {'file_count': 15}}

    assert match_stream_sql_filter(sql_filter, hit)
    assert not match_stream_sql_filter(sql_filter, miss)


def test_select_with_subfields_1():
    sql_filter = """SELECT device.app_version FROM `blah`
                 """
    hit = {'data': {'file_count': 17}, 'device': {'app_version': '4.3.2'}}
    # FIXME: implement 'fail case'
    # miss = {'data': {'file_count': 15}}

    assert {"device.app_version": "4.3.2"} == match_stream_sql_filter(sql_filter, hit)


def test_select_with_subfields_2():
    sql_filter = """SELECT device.app_version FROM `blah` WHERE data.file_count > 16
                 """
    hit = {'data': {'file_count': 17}, 'device': {'app_version': '4.3.2'}}
    miss = {'data': {'file_count': 15}}

    assert {"device.app_version": "4.3.2"} == match_stream_sql_filter(sql_filter, hit)
    assert not match_stream_sql_filter(sql_filter, miss)


def test_select_with_multiple_subfields():
    sql_filter = """SELECT device.app_version,data.file_count FROM `blah` WHERE data.file_count > 16
                 """
    hit = {'data': {'file_count': 17}, 'device': {'app_version': '4.3.2'}}
    miss = {'data': {'file_count': 15}}

    assert {
        "device.app_version": "4.3.2",
        'data.file_count': 17,
    } == match_stream_sql_filter(sql_filter, hit)
    assert not match_stream_sql_filter(sql_filter, miss)


def test_select_with_multiple_subfields_and_space():
    sql_filter = """SELECT device.app_version, data.file_count FROM `blah` WHERE data.file_count > 16
                 """
    hit = {'data': {'file_count': 17}, 'device': {'app_version': '4.3.2'}}
    miss = {'data': {'file_count': 15}}

    assert {
        "device.app_version": "4.3.2",
        'data.file_count': 17,
    } == match_stream_sql_filter(sql_filter, hit)
    assert not match_stream_sql_filter(sql_filter, miss)


def test_select_with_multiple_subfields_and_space_with_aliases_A():
    sql_filter = """SELECT device.app_version AS app_version, data.file_count AS file_count
                    FROM `blah` WHERE data.file_count > 16
                 """
    hit = {'data': {'file_count': 17}, 'device': {'app_version': '4.3.2'}}
    miss = {'data': {'file_count': 15}}

    assert {"app_version": "4.3.2", 'file_count': 17} == match_stream_sql_filter(
        sql_filter, hit
    )
    assert not match_stream_sql_filter(sql_filter, miss)


def test_select_with_multiple_subfields_and_space_with_aliases_B():
    sql_filter = """SELECT device.app_version AS app_version, data.file_count
                    FROM `blah` WHERE data.file_count > 16
                 """
    hit = {'data': {'file_count': 17}, 'device': {'app_version': '4.3.2'}}
    miss = {'data': {'file_count': 15}}

    assert {"app_version": "4.3.2", 'data.file_count': 17} == match_stream_sql_filter(
        sql_filter, hit
    )
    assert not match_stream_sql_filter(sql_filter, miss)


def test_select_with_multiple_subfields_and_space_with_aliases_C():
    sql_filter = """SELECT device.app_version, data.file_count AS file_count
                    FROM `blah` WHERE data.file_count > 16
                 """
    hit = {'data': {'file_count': 17}, 'device': {'app_version': '4.3.2'}}
    miss = {'data': {'file_count': 15}}

    assert {"device.app_version": "4.3.2", 'file_count': 17} == match_stream_sql_filter(
        sql_filter, hit
    )
    assert not match_stream_sql_filter(sql_filter, miss)


def test_select_field_with_zero_integer_value():
    sql_filter = """SELECT data.previous_scene_spent_time FROM `blah` """

    hit = {'data': {"previous_scene_spent_time": 0}}

    assert {"data.previous_scene_spent_time": 0} == match_stream_sql_filter(
        sql_filter, hit
    )


def test_select_field_with_false_boolean_value():
    sql_filter = """SELECT data.on_application_inactive FROM `blah` """

    hit = {'data': {"on_application_inactive": False}}

    assert {"data.on_application_inactive": False} == match_stream_sql_filter(
        sql_filter, hit
    )


def test_select_field_with_empty_string_value():
    sql_filter = """SELECT data.scene_name FROM `blah` """

    hit = {'data': {"scene_name": ""}}

    assert {"data.scene_name": ""} == match_stream_sql_filter(sql_filter, hit)
