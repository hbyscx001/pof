#!/usr/bin/env python3.5
# coding=utf-8

import asyncio
import logging
from enum import Enum
from collections import deque
import struct

import connections
import sock5
import orm

logger = logging.getLogger("default")

STAGE = Enum('SOCK5_STAGE', 'STAGE_INIT STAGE_ADDR STAGE_UDP_ASSOC STAGE_DNS \
             STAGE_CONNECTING STAGE_STREAM STAGE_DESTROYED')

class LocalNegotException(Exception):
    pass

class RemoteConnException(Exception):
    pass

class Server_manager:
    def __init__(self):
        self._wait_connections = deque()
        self._already_connections = deque()
        self._semaphore = asyncio.Semaphore()
        self._orm = orm.Orm()
        self.local_protocol = None

    @asyncio.coroutine
    def server_callback(self, reader, writer):
        local_connection = self.register_connection(reader, writer)
        logger.info("[-] Got connection from {}:{}".format( *local_connection.peer))
        with (yield from self._semaphore):
            self._wait_connections.remove(local_connection)
            self._already_connections.append(local_connection)
            try:
                yield from self.local_protocol.main_dispatch(local_connection)
            # 本地会话连接断开
            except Exception:
                self.close_connection(local_connection)

    def register_connection(self, reader, writer):
        new_connection = connection.Connection(reader, writer)
        self._wait_connections.append(new_connection)
        return new_connection

    def close_connection(self, connection):
        self._already_connections.remove(connection)

