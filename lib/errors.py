class GraphingError(Exception):
    def __init__(self, message: str, *args):
        super().__init__(message, *args)