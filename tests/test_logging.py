from godbot.core.logging import get_logger


def test_logger_creation():
    log = get_logger("test_logger")
    log.info("Logger test message")

    # Basic behavior test
    assert log.name == "test_logger"

