# -*- coding: utf-8 -*-

from unistream.utils import encode_dynamodb_item, decode_dynamodb_item


def test_encode_dynamodb_item():
    pairs = [
        # generic
        ("a_str", {"S": "a_str"}),
        (1, {"N": "1"}),
        (1.0, {"N": "1.0"}),
        (b"a_bytes", {"B": b"a_bytes"}),
        (True, {"BOOL": True}),
        (None, {"NULL": True}),
        # list
        (["a", "b"], {"SS": ["a", "b"]}),
        ([1, 2], {"NS": ["1", "2"]}),
        ([1.0, 2.0], {"NS": ["1.0", "2.0"]}),
        ([b"a", b"b"], {"BS": [b"a", b"b"]}),
        # dict
        ({"key": "a_str"}, {"M": {"key": {"S": "a_str"}}}),
        ({"key": 1}, {"M": {"key": {"N": "1"}}}),
        ({"key": 1.0}, {"M": {"key": {"N": "1.0"}}}),
        ({"key": b"a_bytes"}, {"M": {"key": {"B": b"a_bytes"}}}),
        ({"key": True}, {"M": {"key": {"BOOL": True}}}),
        ({"key": None}, {"M": {"key": {"NULL": True}}}),
    ]
    for v, expected in pairs:
        assert encode_dynamodb_item(v) == expected
    for v, expected in pairs:
        assert decode_dynamodb_item(expected) == v

    # --- nested
    v = [
        {
            "key1": "v1",
            "key2": 2,
            "key3": 3.0,
            "key4": b"v4",
            "key5": True,
            "key6": None,
            "key7": ["a", "b"],
            "key8": [1, 2],
            "key9": [1.0, 2.0],
            "key10": [b"a", b"b"],
            "key11": [
                ["a", "b"],
                # ["1"]
                {"key": "value"},
            ],
        },
    ]
    expected = {
        "L": [
            {
                "M": {
                    "key1": {"S": "v1"},
                    "key2": {"N": "2"},
                    "key3": {"N": "3.0"},
                    "key4": {"B": b"v4"},
                    "key5": {"BOOL": True},
                    "key6": {"NULL": True},
                    "key7": {"SS": ["a", "b"]},
                    "key8": {"NS": ["1", "2"]},
                    "key9": {"NS": ["1.0", "2.0"]},
                    "key10": {"BS": [b"a", b"b"]},
                    "key11": {
                        "L": [
                            {"SS": ["a", "b"]},
                            {"M": {"key": {"S": "value"}}},
                        ]
                    },
                }
            },
        ]
    }
    assert encode_dynamodb_item(v) == expected
    assert decode_dynamodb_item(expected) == v


if __name__ == "__main__":
    from unistream.tests import run_cov_test

    run_cov_test(__file__, "unistream.utils", preview=False)
