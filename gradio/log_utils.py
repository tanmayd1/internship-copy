import logging
import io


class StringIOHandler(logging.Handler):
    """
    A custom logging handler that captures log messages in a StringIO object.
    This allows capturing log messages in memory and later retrieving them.
    """

    def __init__(self):
        """
        Initializes the StringIOHandler by setting up the StringIO object.
        """
        super().__init__()
        self.log_capture_string = io.StringIO()

    def emit(self, record):
        """
        Writes a formatted log record to the StringIO object.

        Args:
            record (logging.LogRecord): The log record to be formatted and written.
        """
        message = self.format(record)
        self.log_capture_string.write(message + '\n')

    def get_log_contents(self):
        """
        Retrieves the contents of the log messages captured in the StringIO object.

        Returns:
            str: All log messages captured so far.
        """
        return self.log_capture_string.getvalue()


def parse_validation_log(log):
    """
    Parses a validation log to separate errors from warnings.

    Args:
        log (str): The log string containing validation messages.

    Returns:
        tuple: Two lists, one containing error messages and the other containing warning messages.
    """
    errors = []
    warnings = []
    for line in log.split('\n'):
        if 'error' in line.lower():
            errors.append(line.strip())
        elif 'warning' in line.lower():
            warnings.append(line.strip())
    return errors, warnings


# Create an instance of the custom log handler
log_handler = StringIOHandler()
# Configure the logging to use the custom handler and set the level to WARNING
logging.basicConfig(level=logging.WARNING, handlers=[log_handler])
