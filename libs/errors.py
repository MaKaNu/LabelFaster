class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class InputError(Error):
    """Exception raised for error in the input (standard just input and
    standard message)

    Attributes:
        input -- the value which caused the array
        message -- explanation of the error
    """

    def __init__(self, input, message='Wrong Input Value'):
        self.input = input
        self.message = message
        super().__init__(self.message)
