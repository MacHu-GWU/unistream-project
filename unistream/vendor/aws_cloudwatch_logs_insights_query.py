# -*- coding: utf-8 -*-

"""
A helper module to work with CloudWatch Logs Group, Stream, put log events,
and query logs insights.

Requirements:

- Python: 3.7+
- Dependencies:

    # content of requirements.txt
    boto3
    func_args>=0.1.1,<1.0.0

Usage:

.. code-block:: python

    from aws_cloudwatch_logs_insights_query import (
        get_log_group,
        create_log_group,
        delete_log_group,
        get_log_stream,
        create_log_stream,
        delete_log_stream,
        Event,
        BaseJsonMessage,
        put_log_events,
        get_ts_in_second,
        get_ts_in_millisecond,
        QueryStatusEnum,
        wait_logs_insights_query_to_succeed,
        run_query,
        extract_query_results,
    )
"""

import typing as T
import time
import json
import enum
import dataclasses
from datetime import datetime, timezone, timedelta

import botocore.exceptions
from func_args import NOTHING, resolve_kwargs

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_logs import CloudWatchLogsClient
    from mypy_boto3_logs.type_defs import (
        LogGroupTypeDef,
        LogStreamTypeDef,
        PutLogEventsResponseTypeDef,
        GetQueryResultsResponseTypeDef,
    )

__version__ = "0.1.1"

# ------------------------------------------------------------------------------
# Idempotent API
#
# CRUD for log group and stream in boto3 is not idempotent, they don't check
# if the resource already exists or not. So we made some improvements.
#
# - get_xyz:
# - create_xyz:
# - delete_xyz:
# ------------------------------------------------------------------------------
# --- Log Group ---
def get_log_group(
    logs_client: "CloudWatchLogsClient",
    group_name: str,
) -> T.Optional[T.Union[dict, "LogGroupTypeDef"]]:
    """
    Get a log group details by name, if it doesn't exist, return None.

    Ref:

    - describe_log_groups: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs/client/describe_log_groups.html

    :return: A dict with the log group details, or None if it doesn't exist.
    """
    res = logs_client.describe_log_groups(
        logGroupNamePrefix=group_name,
    )
    groups = [
        dct
        for dct in res.get("logGroups", [])
        if dct.get("logGroupName", "******") == group_name
    ]
    if len(groups) == 1:
        return groups[0]
    else:
        return None


def create_log_group(
    logs_client: "CloudWatchLogsClient",
    group_name: str,
    kms_key_id: str = NOTHING,
    tags: T.Dict[str, str] = NOTHING,
) -> bool:
    """
    Create a log group, if it already exists, do nothing.

    Ref:

    - create_log_group: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs/client/create_log_group.html

    :return: True if the log group was created, False if it already existed.
    """
    try:
        logs_client.create_log_group(
            **resolve_kwargs(
                logGroupName=group_name,
                kmsKeyId=kms_key_id,
                tags=tags,
            )
        )
        return True
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ResourceAlreadyExistsException":
            return False
        else:  # pragma: no cover
            raise e


def delete_log_group(
    logs_client: "CloudWatchLogsClient",
    group_name: str,
) -> bool:
    """
    Delete a log group, if it doesn't exist, do nothing.

    Ref:

    - delete_log_group: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs/client/delete_log_group.html

    :return: True if the log group was deleted, False if it didn't exist.
    """
    try:
        logs_client.delete_log_group(
            logGroupName=group_name,
        )
        return True
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            return False
        else:  # pragma: no cover
            raise e


# --- Log Stream ---
def get_log_stream(
    logs_client: "CloudWatchLogsClient",
    group_name: str,
    stream_name: str,
) -> T.Optional[T.Union[dict, "LogStreamTypeDef"]]:
    """
    Get a log stream details by name, if it doesn't exist, return None.

    Ref:

    - describe_log_streams: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs/client/describe_log_streams.html

    :return: A dict with the log stream details, or None if it doesn't exist.
    """
    res = logs_client.describe_log_streams(
        logGroupName=group_name,
        logStreamNamePrefix=stream_name,
    )
    streams = [
        dct
        for dct in res.get("logStreams", [])
        if dct.get("logStreamName", "unknown-log-stream-name") == stream_name
    ]
    if len(streams):
        return streams[0]
    else:
        return None


def create_log_stream(
    logs_client: "CloudWatchLogsClient",
    group_name: str,
    stream_name: str,
) -> bool:
    """
    Create a log stream, if it already exists, do nothing.

    Ref:

    - create_log_stream: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs/client/create_log_stream.html

    :return: True if the log stream was created, False if it already existed.
    """
    try:
        logs_client.create_log_stream(
            logGroupName=group_name,
            logStreamName=stream_name,
        )
        return True
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ResourceAlreadyExistsException":
            return False
        else:  # pragma: no cover
            raise e


def delete_log_stream(
    logs_client: "CloudWatchLogsClient",
    group_name: str,
    stream_name: str,
) -> bool:
    """
    Delete a log stream, if it doesn't exist, do nothing.

    Ref:

    - delete_log_stream: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs/client/delete_log_stream.html

    :return: True if the log stream was deleted, False if it didn't exist.
    """
    try:
        logs_client.delete_log_stream(
            logGroupName=group_name,
            logStreamName=stream_name,
        )
        return True
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            return False
        else:  # pragma: no cover
            raise e


# ------------------------------------------------------------------------------
# Idempotent API
#
# CRUD for log group and stream in boto3 is not idempotent, they don't check
# if the resource already exists or not. So we made some improvements.
#
# - get_xyz:
# - create_xyz:
# - delete_xyz:
# ------------------------------------------------------------------------------
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def get_utc_now() -> datetime:
    return datetime.utcnow().replace(tzinfo=timezone.utc)


def get_utc_now_ts() -> int:
    """
    The put log events API expects a timestamp in milliseconds since epoch.
    """
    return get_ts_in_millisecond(get_utc_now())


@dataclasses.dataclass
class Event:
    """
    Log event data model.
    """

    message: str = dataclasses.field()
    timestamp: int = dataclasses.field(default_factory=get_utc_now_ts)


@dataclasses.dataclass
class BaseJsonMessage:
    """
    Base class for json encoded log message.
    """

    def to_json(self) -> str:
        """
        Convert the object to a json string.

        You can override this method to customize the json serialization.
        """
        return json.dumps(dataclasses.asdict(self))

    @classmethod
    def from_json(cls, json_str: str):  # pragma: no cover
        """
        You can override this module to customize the json deserialization.
        """
        dct = json.loads(json_str)
        return cls(**dct)


def put_log_events(
    logs_client: "CloudWatchLogsClient",
    group_name: str,
    stream_name: str,
    events: T.List[Event],
    auto_create_stream: bool = True,
) -> T.Optional[T.Union[dict, "PutLogEventsResponseTypeDef"]]:
    """
    Put a list of events into a log stream.

    Ref:

    - put_log_events: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs/client/put_log_events.html

    :param logs_client: The boto3 logs client.
    :param group_name: The log group name.
    :param stream_name: The log stream name.
    :param events: A list of :class:`Event` objects.
    :param auto_create_stream: if True, f log stream doesn't exist,
        automatically create it.

    :return: A dict with the response from the put_log_events call.
    """
    if len(events) == 0:  # pragma: no cover
        return None
    kwargs = dict(
        logGroupName=group_name,
        logStreamName=stream_name,
        logEvents=[dataclasses.asdict(event) for event in events],
    )
    try:
        res = logs_client.put_log_events(**kwargs)
        return res
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            if "log stream" in str(e):
                if auto_create_stream:
                    create_log_stream(logs_client, group_name, stream_name)
                    res = logs_client.put_log_events(**kwargs)
                    return res
        raise e  # pragma: no cover


def get_ts(dt: datetime) -> float:
    """
    Convert a datetime object to a timestamp in seconds since epoch.

    It assumes the datetime object is in UTC if it doesn't have a timezone.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return (dt - EPOCH).total_seconds()


def get_ts_in_second(dt: datetime) -> int:
    """
    Convert a datetime object to a timestamp in seconds since epoch.
    """
    return int(get_ts(dt))


def get_ts_in_millisecond(dt: datetime) -> int:
    """
    Convert a datetime object to a timestamp in milliseconds since epoch.
    """
    return int(get_ts(dt) * 1000)


class QueryStatusEnum(str, enum.Enum):
    """
    Enum for the query status.

    Ref: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs/client/get_query_results.html
    """

    Scheduled = "Scheduled"
    Running = "Running"
    Complete = "Complete"
    Failed = "Failed"
    Cancelled = "Cancelled"
    Timeout = "Timeout"
    Unknown = "Unknown"


def wait_logs_insights_query_to_succeed(
    logs_client: "CloudWatchLogsClient",
    query_id: str,
    delta: int = 1,
    timeout: int = 30,
) -> T.Union[dict, "GetQueryResultsResponseTypeDef"]:
    """
    Wait a given athena query to reach ``Complete`` status. If failed,
    raise ``RuntimeError`` immediately. If timeout, raise ``TimeoutError``.

    Ref:

    - get_query_results: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs/client/get_query_results.html

    :param logs_client: The boto3 cloudwatch logs client.
    :param query_id: The query id from the response of ``start_query`` API call.
    :param delta: The time interval in seconds between each query status check.
    :param timeout: The maximum time in seconds to wait for the query to succeed.
    """
    elapsed = 0
    for _ in range(999999):
        res = logs_client.get_query_results(queryId=query_id)
        status = res["status"]
        if status == QueryStatusEnum.Complete.value:
            return res
        elif status in [
            QueryStatusEnum.Failed.value,
            QueryStatusEnum.Cancelled.value,
            QueryStatusEnum.Timeout.value,
        ]:  # pragma: no cover
            raise RuntimeError(f"query {query_id} reached status: {status}")
        else:
            time.sleep(delta)
        elapsed += delta
        if elapsed > timeout:  # pragma: no cover
            raise TimeoutError(f"logs insights query timeout in {timeout} seconds!")


def strip_out_limit_clause(query: str) -> str:
    """
    Strip out the limit clause from a query string.
    """
    lines = query.splitlines()
    return "\n".join([line for line in lines if not line.startswith("| limit")])


def get_time_range(
    last_n_minutes: T.Union[int, float] = 0,
    last_n_hours: T.Union[int, float] = 0,
    last_n_days: T.Union[int, float] = 0,
) -> T.Tuple[datetime, datetime]:
    """
    Calculate the start and end datetime for a given time range.
    """
    if all(
        [last_n_minutes == 0, last_n_hours == 0, last_n_days == 0]
    ):  # pragma: no cover
        raise ValueError
    end_datetime = get_utc_now()
    start_datetime = end_datetime - timedelta(
        days=last_n_days,
        hours=last_n_hours,
        minutes=last_n_minutes,
    )
    return start_datetime, end_datetime


def run_query(
    logs_client: "CloudWatchLogsClient",
    query: str,
    log_group_name: T.Optional[str] = NOTHING,
    log_group_name_list: T.Optional[T.List[str]] = NOTHING,
    log_group_id_list: T.Optional[T.List[str]] = NOTHING,
    start_datetime: T.Optional[datetime] = None,
    end_datetime: T.Optional[datetime] = None,
    last_n_minutes: T.Optional[int] = 0,
    last_n_hours: T.Optional[int] = 0,
    last_n_days: T.Optional[int] = 0,
    limit: int = 1000,
    wait: bool = True,
    delta: int = 1,
    timeout: int = 30,
) -> T.Tuple[str, T.Optional[T.Union[dict, "GetQueryResultsResponseTypeDef"]]]:
    """
    Run a logs insights query and wait for the query to succeed. It is a more
    human friendly wrapper of the ``start_query`` and ``get_query_results`` API.

    Ref: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs/client/start_query.html

    :param logs_client: The boto3 cloudwatch logs client.
    :param query: The query string. don't use ``| limit abc`` in your query,
        use the ``limit`` parameter instead.
    :param log_group_name: see ``start_query`` API.
    :param log_group_name_list: see ``start_query`` API.
    :param log_group_id_list: see ``start_query`` API.
    :param start_datetime: python datetime object for start time,
        if timezone is not set, it assumes UTC.
    :param end_datetime: python datetime object for end time,
        if timezone is not set, it assumes UTC.
    :param last_n_minutes: query the time range from now to ``last_n_minutes`` ago.
    :param last_n_hours: query the time range from now to ``last_n_hours`` ago.
    :param last_n_days: query the time range from now to ``last_n_days`` ago.
    :param wait: if True, wait until query succeeded and return the query result,
        otherwise return the query id only and set query result as None.
    :param limit: see ``start_query`` API.
    :param delta: The time interval in seconds between each query status check.
    :param timeout: The maximum time in seconds to wait for the query to succeed.
    """
    # resolve start and end time
    if start_datetime is None and end_datetime is None:
        start_datetime, end_datetime = get_time_range(
            last_n_minutes=last_n_minutes,
            last_n_hours=last_n_hours,
            last_n_days=last_n_days,
        )
    # resolve start_query kwargs
    start_ts = get_ts_in_second(start_datetime)
    end_ts = get_ts_in_second(end_datetime)
    kwargs = dict(
        logGroupName=log_group_name,
        logGroupNames=log_group_name_list,
        logGroupIds=log_group_id_list,
        startTime=start_ts,
        endTime=end_ts,
        queryString=query,
        limit=limit,
    )
    # run query
    res = logs_client.start_query(**resolve_kwargs(**kwargs))
    # get results
    query_id = res["queryId"]
    if wait:
        res = wait_logs_insights_query_to_succeed(logs_client, query_id, delta, timeout)
    else:  # pragma: no cover
        res = None
    return query_id, res


def extract_query_results(response: dict) -> T.List[dict]:
    """
    The ``get_query_results`` API response returns the query results in a
    list of key value pair format. Human usually prefer dict format. This function
    can extract the ``results`` field and reformat it to a list of dict.

    .. code-block:: python

        {
            'results': [
                [
                    {
                        'field': 'string',
                        'value': 'string'
                    },
                    {
                        'field': 'string',
                        'value': 'string'
                    },
                    ...
                ],
            ],
            ...
        }

    :param response: the response from ``get_query_results`` API call.

    :return: a list of dict.
    """
    return [
        {dct["field"]: dct["value"] for dct in result}
        for result in response.get("results", [])
    ]
