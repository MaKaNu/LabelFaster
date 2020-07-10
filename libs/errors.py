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


class ValueError(Error):
    """Exception raised for error in the value (standard just input and
    standard message)

    Attributes:
        value -- the value which caused while setting
        message -- explanation of the error
    """

    def __init__(self, value, message='Wrong value'):
        self.value = value
        self.message = message
        super().__init__(self.message)


class ClassesError(Error):
    def __init__(self, value, message='Some Problems with LabelClasses'):
        self.value = value
        self.message = message
        super().__init__(self.message)
