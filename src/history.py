

class Log:
    def __init__(self, idx, prev_value, new_value) -> None:
        self.idx = idx
        self.prev_value = prev_value
        self.new_value = new_value


class History:
    def __init__(self) -> None:
        self.logs = []
        self.i = 0

    def add_log(self, log: Log) -> None:
        if self.i < len(self.logs):
            self.logs = self.logs[:self.i]
        self.logs.append(log)
        self.i += 1

    def undo(self) -> Log:
        if self.i == 0:
            return None
        self.i -= 1
        return self.logs[self.i]

    def redo(self) -> Log:
        if self.i == len(self.logs):
            return None
        self.i += 1
        return self.logs[self.i - 1]
