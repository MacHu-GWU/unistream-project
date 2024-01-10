# -*- coding: utf-8 -*-

import typing as T
from datetime import datetime, timezone

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
EPOCH_STR = EPOCH.isoformat()


def get_utc_now() -> datetime:
    return datetime.utcnow().replace(tzinfo=timezone.utc)


def encode_dynamodb_item(
    v: T.Union[
        str,
        int,
        float,
        bytes,
        bool,
        None,
        list,
        dict,
    ],
) -> T.Dict[str, T.Any]:
    """
    Encode arbitrary value to ``item`` argument in the
    ``boto3("dynamodb").put_item`` API call.
    """
    if isinstance(v, str):
        return {"S": v}
    elif isinstance(v, bool):
        return {"BOOL": v}
    elif isinstance(v, (int, float)):
        return {"N": str(v)}
    elif isinstance(v, bytes):
        return {"B": v}
    elif v is None:
        return {"NULL": True}
    elif isinstance(v, dict):
        return {"M": {key: encode_dynamodb_item(value) for key, value in v.items()}}
    elif isinstance(v, list):
        if len(v):
            i = v[0]
            if isinstance(i, str):
                return {"SS": v}
            elif isinstance(i, (int, float)):
                return {"NS": [str(i) for i in v]}
            elif isinstance(i, bytes):
                return {"BS": v}
            elif isinstance(i, list):
                return {"L": [encode_dynamodb_item(i) for i in v]}
            elif isinstance(i, dict):
                return {"L": [encode_dynamodb_item(i) for i in v]}
        else:
            return {"L": []}


def decode_dynamodb_item(
    v: T.Dict[str, T.Any],
) -> T.Union[str, int, float, bytes, bool, None, list, dict,]:
    if "S" in v:
        return v["S"]
    elif "BOOL" in v:
        return v["BOOL"]
    elif "N" in v:
        return float(v["N"]) if "." in v["N"] else int(v["N"])
    elif "B" in v:
        return v["B"]
    elif "NULL" in v:
        return None
    elif "M" in v:
        return {key: decode_dynamodb_item(value) for key, value in v["M"].items()}
    elif "SS" in v:
        return v["SS"]
    elif "NS" in v:
        return [float(i) if "." in i else int(i) for i in v["NS"]]
    elif "BS" in v:
        return v["BS"]
    elif "L" in v:
        return [decode_dynamodb_item(i) for i in v["L"]]
    else:
        raise ValueError(f"Unknown type: {v}")
