from enum import IntEnum
import time
from datetime import datetime
import threading
from typing import List
from abc import ABC, abstractmethod

class LogLevel(IntEnum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    FATAL = 3
    ERROR = 4

class LogMessage:
    def __init__(self, msg: str, level: LogLevel):
        self.msg = msg
        self.level: LogLevel = level
        self.timestamp = datetime.now()

class LogAppender(ABC):
    @abstractmethod
    def append_log(self, log: LogMessage):
        pass


class ConsoleAppender(LogAppender):
    def append_log(self, log: LogMessage):
        print(f'[{log.level.name} -- {log.timestamp} -- {log.msg}]')
    
class LoggerConfig:
    def __init__(self, min_level: LogLevel = LogLevel.INFO):
        self.min_level = min_level
        self.appenders: List[LogAppender] = []
        self.lock = threading.Lock()

    def add_appender(self, appender: LogAppender):
        with self.lock:
            self.appenders.append(appender)

    def set_level(self, level: LogLevel):
        with self.lock:
            self.min_level = level

class Logger:
    instance = None
    lock = threading.Lock()

    def __new__(cls):
        if cls.instance is None:
            with cls.lock:
                if cls.instance is None:
                    cls.instance = super(Logger, cls).__new__(cls)
                    cls.instance.initialize()
        return cls.instance
    
    def initialize(self):
        self.config = LoggerConfig()

    def set_config(self, config: LoggerConfig):
        with self.lock:
            self.config = config
        
    def log(self, level: LogLevel, msg: str):
        if level >= self.config.min_level:
            log_msg = LogMessage(msg, level)

            for appender in self.config.appenders:
                appender.append_log(log_msg)
    
    def info(self, msg: str):
        self.log(LogLevel.INFO, msg)

    def debug(self, msg: str):
        self.log(LogLevel.DEBUG, msg)


def demo():
    logger = Logger()

    config = LoggerConfig(min_level=LogLevel.INFO)

    config.add_appender(ConsoleAppender())
    logger.set_config(config)

    logger.info("Hello world!")
    logger.debug("debug log")
    
if __name__ == "__main__":
    demo()