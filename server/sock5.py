#!/usr/bin/env python3
# coding=utf-8

import asyncio
from enum import Enum
from abc import abstractmethod



class Protocol_helper:
    def __init__(self):
        self._state = None

    # 主要的协议状态机驱动
    @abstractmethod
    def main_dispatch(self):
        pass


class Protocol_helper_SOCK5(Protocol_helper):
    STATE = Enum('SOCK5_STATE', 'STATE_INIT STATE_ADDR STATE_UDP STAGE_DNS \
                 STATE_CONNECTING STAGE_STREAM STATE_DESTORYED')

    def __init__(self, manager, remote_protocol=None):
        self._manager = manager
        self._remote_protocol = remote_protocol

    @asyncio.coroutine
    def main_dispatch(self, local_connection):
        remote_connection = None
        local_connection.stage = Protocol_helper_SOCK5.STATE_INIT
        while True:
            if local_connection.stage == Protocol_helper_SOCK5.STAGE.STATE_INIT:
                yield from self.stage_init(local_connection)
            elif local_connection.stage == Protocol_helper_SOCK5.STAGE.STAGE_ADDR:
                remote_connection = yield from self.stage_addr(local_connection)
            elif local_connection.stage == Protocol_helper_SOCK5.STAGE_CONNECTING:
                yield from self.stage_connecting(local_connection)
            elif local_connection.stage == Protocol_helper_SOCK5.STAGE_STREAM:
                yield from self.stage_stream(local_connection, remote_connection)
            elif local_connection.stage == Protocol_helper_SOCK5.STAGE_DESTROYED:
                local_connection.close()
            else:
                raise Exception

    @asyncio.coroutine
    def stage_connecting(self, local_connection):
        ver, nuser = struct.unpack('!BB', (yield from local_connection.read(2)))
        username, npass = struct.unpack('!{}sB', (yield from local_connection.read(nuser+1)))
        password = struct.unpack('!{}s', (yield from local_connection.read(npass)))
        user = orm.authority(username, password)
        if user:
            yield from local_connection.write(b'\x05\x01')
            logger.info("User:{} login successful {}:{}".format( user, *local_connection.peer))
            self._stage = Protocol_helper_SOCK5.STAGE.STAGE_ADDR
        else:
            yield from local_connection.write(b'\x05\x00')
            logger.warning("Login failed {}:{}".format( *local_connection.peer))
            local_connection.stage = Protocol_helper_SOCK5.STAGE.STAGE_DESTROYED

    @asyncio.coroutine
    def stage_init(self, local_connection):
        ver, nmethod = struct.unpack('!BB', (yield from local_connection.read(2)))
        methods = struct.unpack('!{}B', (yield from local_connection.read(nmethod)))
        if 0x03 not in methods:
            raise Connection_lost
        yield from local_connection.write(b'\x05\x03')
        local_connection.stage = Protocol_helper_SOCK5.STAGE_CONNECTING

    @asyncio.coroutine
    def stage_addr(self, local_connection):
        try:
            ver, cmd, rsv, atyp = struct.unpack('!BBBB', (yield from local_connection.read(4)))
            if atyp == 0x01:
                naddr = 6
                str_addr, port = struct.unpack('!{}sH', (yield from local_connection.read(naddr + 2)))
                addr = '.'.join(map(ord, str_addr))
            elif atyp == 0x03:
                naddr = struct.unpack('B', (yield from local_connection.read(1)))
                str_addr, port = struct.unpack('!{}sH', (yield from local_connection.read(naddr + 2)))
                addr = str_addr
            else:
                self._stage = Protocol_helper_SOCK5.STAGE.STAGE_DESTROYED

            (reader, writer) = asyncio.open_connection(addr, port)
            remote_connection = connection.Connection(reader, writer)
            strs = struct.pack('!BBBB{}sH'.format(naddr), 0x05, 0x00, 0x00, str_addr, port)
            yield from local_connection.write(strs)
            logger.info("Delay {}:{} to {}:{}".format( *local_connection.peer, addr, port))
            local_connection.stage = Protocol_helper_SOCK5.STAGE_STREAM
            return remote_connection
        except Exception:
            local_connection.stage = Protocol_helper_SOCK5.STAGE_DESTROYED

    @asyncio.coroutine
    def stage_stream(self, local_connection, remote_connection):
        client_coro = local_connection.coro_pipe(remote_connection)
        remote_coro = remote_connection.coro_pipe(local_connection)
        coro = asyncio.wait([client_coro, remote_coro])
        try:
            results = yield from coro
            upload_bytes = local_connection._read_bytes
            download_bytes = local_connection._write_bytes
            logger.info("FROM {} TO {} uploads:{} download:{}".format(
                local_connection.peer, remote_connection.peer, upload_bytes, download_bytes
            ))
        except:
            local_connection.clear()
            remote_connection.clear()
            yield from local_connection.read()
            yield from asyncio.sleep(0.1)
            local_connection.stage = Protocol_helper_SOCK5.STAGE_ADDR

