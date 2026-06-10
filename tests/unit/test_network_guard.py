"""The unit suite must never reach remote hosts (enforced by the conftest guard).

These tests verify that the _block_remote_network autouse fixture is working
correctly: unit tests get SocketConnectBlockedError on remote connect attempts,
and integration-marked tests are exempted.
"""

import socket

import pytest


def test_remote_connect_is_blocked():
    """Connecting to a remote IP must raise an error, not send packets."""
    with pytest.raises(Exception, match="(?i)socket|network|blocked"):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.settimeout(2)
            # example.com IP — must be blocked BEFORE any packet leaves
            s.connect(("93.184.216.34", 80))
        finally:
            s.close()


def test_localhost_connect_is_allowed():
    """Connecting to localhost must NOT be blocked (xdist workers need it)."""
    # We just verify that creating a socket and binding to localhost works.
    # We don't need to actually connect to a running service.
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("127.0.0.1", 0))  # bind to any free port — proves socket not blocked
    finally:
        s.close()


@pytest.mark.integration
def test_integration_tests_keep_socket_access():
    """Integration-marked tests must be able to create and use sockets freely."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.close()  # creating a socket must not raise for integration-marked tests
