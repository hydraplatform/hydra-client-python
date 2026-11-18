"""RemoteJSONConnection with a bearer token: sent as a header, with no session cookie, and no login."""
from unittest import mock

from hydra_client.connection import RemoteJSONConnection


def _response():
    r = mock.Mock(ok=True, content=b'{"id": 1}', cookies={'beaker.session.id': 'should-not-be-kept'})
    return r


def test_bearer_token_is_sent_as_a_header_without_cookies():
    conn = RemoteJSONConnection('http://hydra.test', bearer_token='tok123')
    with mock.patch('hydra_client.connection.remote_json_connection.requests.post', return_value=_response()) as post:
        conn.call('whoami')
    kwargs = post.call_args.kwargs
    assert kwargs['headers']['Authorization'] == 'Bearer tok123'
    assert kwargs['cookies'] == {}
    assert conn.session_id is None


def test_without_a_token_nothing_changes():
    conn = RemoteJSONConnection('http://hydra.test', session_id='abc')
    with mock.patch('hydra_client.connection.remote_json_connection.requests.post', return_value=_response()) as post:
        conn.call('whoami')
    kwargs = post.call_args.kwargs
    assert 'Authorization' not in kwargs['headers']
    assert kwargs['cookies']['beaker.session.id'] == 'abc'
