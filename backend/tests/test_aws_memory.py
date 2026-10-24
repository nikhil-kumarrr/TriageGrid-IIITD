from unittest.mock import MagicMock
from triagegrid.services.memory.aws_provider import AWSMemoryProvider


def provider(table):
    p = AWSMemoryProvider.__new__(AWSMemoryProvider)
    p.table_name = 'triagegrid_memory'
    p._client = MagicMock()
    p._client.Table.return_value = table
    p._checked_at = 0.0
    p._reachable = False
    return p


def message(n):
    return {'id': str(n), 'role': 'user', 'text': 'Synthetic test', 'created': str(n)}


def test_history_queries_sort_key_and_returns_recent_messages_chronologically():
    table = MagicMock()
    table.query.side_effect = [
        {'Items': [message(3)], 'LastEvaluatedKey': {'session_id': 'a', 'sk': 'MSG#3'}},
        {'Items': [message(2)]},
    ]
    p = provider(table)
    assert [m.id for m in p.get_history('a', 2)] == ['2', '3']
    query = table.query.call_args_list[0].kwargs
    assert query['KeyConditionExpression'] == 'session_id = :sid AND begins_with(sk, :prefix)'
    assert query['ExpressionAttributeValues'] == {':sid': 'a', ':prefix': 'MSG#'}
    assert query['ScanIndexForward'] is False
    assert table.query.call_args_list[1].kwargs['Limit'] == 1
    assert 'ExclusiveStartKey' in table.query.call_args_list[1].kwargs


def test_clear_deletes_all_pages_only_in_requested_session():
    table = MagicMock()
    table.query.side_effect = [
        {'Items': [{'session_id': 'a', 'sk': 'MSG#1'}], 'LastEvaluatedKey': {'session_id': 'a', 'sk': 'MSG#1'}},
        {'Items': [{'session_id': 'a', 'sk': 'FACTS'}]},
    ]
    p = provider(table)
    p.clear('a')
    assert table.query.call_count == 2
    batch = table.batch_writer.return_value.__enter__.return_value
    assert batch.delete_item.call_count == 2
    for call in table.query.call_args_list:
        assert call.kwargs['ExpressionAttributeValues'] == {':sid': 'a'}


def test_readiness_requires_active_reachable_table():
    p = provider(MagicMock())
    p._client.meta.client.describe_table.return_value = {'Table': {'TableStatus': 'ACTIVE'}}
    assert p.is_configured()
    assert p.is_configured()
    assert p._client.meta.client.describe_table.call_count == 1
    p._checked_at = 0
    p._client.meta.client.describe_table.side_effect = RuntimeError('Unreachable')
    assert not p.is_configured()
