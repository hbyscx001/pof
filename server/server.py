#!/usr/bin/env python3
# coding=utf-8

import asyncio
import logging

from sock_manager import Server_manager
from config import got_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # 配置类，server_config 包含eventloop.create_server的运行参数
    # configer = got_config()

    loop = asyncio.get_event_loop()

    coro = asyncio.start_server(Server_manager().server_callback,
                                                            '127.0.0.1',8888)
    server = loop.run_until_complete(coro)

    logger.info("Serving on {}".format(server.sockets[0].getsockname()))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.warning("Got signal exit")

    server.close()
    loop.run_until_complete(server.wait_closed())
    logger.info("Server STOP")
    loop.close()


if __name__ == '__main__':
    main()
