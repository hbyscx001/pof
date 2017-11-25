#!/usr/bin/env python3
# coding=utf-8

import asyncio

from crypter import Default_crypter

class Connection_lost(Exception):
    pass

class Connection:
    # def __init__(self, reader, writer, crypter=None):
    def __init__(self, reader, writer, crypter=None):
        self.peer = writer.get_extra_info('peername')

        self._reader = reader
        self._read_bytes = 0
        self._writer = writer
        self._write_bytes = 0
        self._crypter = crypter or Default_crypter()
        self._stage = None

    @asyncio.coroutine
    def read(self, n=-1):
        crypt_data = yield from self._reader.read(n)
        self._read_bytes += len(crypt_data)
        return self._crypter.decrypt(crypt_data)

    @asyncio.coroutine
    def write(self, data):
        crypt_data = self._crypter.encrypt(data)
        self._write_bytes += len(crypt_data)
        self._writer.write(data)
        yield from self._writer.drain()

    @asyncio.coroutine
    def coro_pipe(self, outer_conn):
        while True:
            data = yield from self.read()
            yield from outer_conn.write(data)

    def clear(self):
        self._read_bytes = 0
        self._write_bytes = 0

    def close(self):
        self._writer.close()

    @property
    def stage(self):
        return self._stage

    @stage.set
    def stage(self, value):
        self._stage = value

if __name__ == '__main__':

    @asyncio.coroutine
    def test():
        reader, writer = yield from asyncio.open_connection('127.0.0.1', 8888)
        test_con = Connection(reader, writer)
        yield from test_con.write(b"Hello world")
        loop.stop()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())


