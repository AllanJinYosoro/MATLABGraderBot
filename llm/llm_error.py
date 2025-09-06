class ResponseParseError(Exception):
    """解析模型输出失败时抛出的异常"""
    def __init__(self, message: str, raw_output: str, tokens: int):
        super().__init__(message)
        self.raw_output = raw_output
        self.tokens = tokens