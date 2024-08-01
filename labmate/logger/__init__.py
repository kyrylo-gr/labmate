import io
import logging
import sys


class BufferCatcher(io.StringIO):
    _last_value = None

    @property
    def last_value(self):
        if self._last_value is None:
            return self.getvalue()
        return self._last_value

    def close(self) -> None:
        self._last_value = self.getvalue()
        return super().close()


class StreamHandler(logging.StreamHandler):
    stream: io.StringIO

    def __init__(self, stream=None):
        if stream is None:
            stream = io.StringIO()
        super().__init__(stream)

    def reset(self):
        self.stream.close()
        stream = io.StringIO()
        self.setStream(stream)


class Logger(logging.Logger):
    stdout_message: str

    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)

        self.logger_handler = StreamHandler()
        logger_formatter = logging.Formatter(
            "%(name)s:%(filename)s:%(asctime)s:\n%(levelname)s:%(message)s"
        )
        self.logger_handler.setFormatter(logger_formatter)
        self.logger_handler.setLevel(logging.DEBUG)
        self.addHandler(self.logger_handler)

        logger_handler_short = logging.StreamHandler()
        logger_formatter_short = logging.Formatter("%(levelname)s:%(message)s")
        logger_handler_short.setFormatter(logger_formatter_short)
        logger_handler_short.setLevel(logging.INFO)
        self.addHandler(logger_handler_short)

        self.propagate = False
        self.stdout_buffer = BufferCatcher()
        self.stdout_message = ""

    def reset(self):
        self.logger_handler.reset()

        self.stdout_setup()
        self.stdout_message = ""

    def stdout_flush(self):
        self.stdout_message += f"\n{self.stdout_buffer.last_value}"
        self.stdout_setup()

    def stdout_setup(self):
        self.stdout_buffer = BufferCatcher()
        sys.stdout._buffer = self.stdout_buffer  # type: ignore # pylint: disable=protected-access

    def getvalue(self):
        return self.logger_handler.stream.getvalue()

    def get_stdout(self):
        return self.stdout_message + f"\n{self.stdout_buffer.last_value}"


logger = Logger("Labmate")
