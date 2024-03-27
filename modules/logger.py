"""
Модуль логов
by MrWoon
"""

import logging

class Logger:
    def __init__(self, name, file=None):
        self.name = name
        self.file = file
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s | %(name)s | [%(levelname)s] %(message)s', datefmt='%d.%m.%Y %H:%M')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        if file:
            file_handler = logging.FileHandler(file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def log(self, level, content):
        if level.lower() == 'info':
            self.logger.info(content)
        elif level.lower() == 'warn':
            self.logger.warning(content)
        elif level.lower() == 'error':
            self.logger.error(content)
        elif level.lower() == 'critical':
            self.logger.critical(content)
        elif level.lower() == 'debug':
            self.logger.debug(content)
        else:
            self.logger.error("Invalid log level")