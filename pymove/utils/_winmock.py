class WindowsUser:
    """Mock class for module errors on windows."""

    def __init__(self):
        """Instantiates mock class."""
        self.pw_name = "windows"


def getpwuid(uid):
    """Default value for pwd on windows."""
    return WindowsUser()