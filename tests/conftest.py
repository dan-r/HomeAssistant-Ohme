"""Global fixtures for custom integration."""
import pytest_socket

def enable_external_sockets():
    pytest_socket.enable_socket()
