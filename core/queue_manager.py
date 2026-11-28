import random

REPEAT_OFF = "off"
REPEAT_ALL = "all"
REPEAT_ONE = "one"


class PlayQueue:
    def __init__(self):
        self.current = -1
        self.shuffle = False
        self.repeat = REPEAT_OFF
        self.history = []

    def next_index(self, count, auto=False):
        if count == 0:
            return None
        if auto and self.repeat == REPEAT_ONE:
            return self.current
        if self.shuffle:
            if self.current != -1:
                self.history.append(self.current)
            choices = [i for i in range(count) if i != self.current]
            return random.choice(choices) if choices else self.current

        following = self.current + 1
        if following >= count:
            if self.repeat == REPEAT_ALL or not auto:
                return 0
            return None
        return following

    def previous_index(self, count):
        if count == 0:
            return None
        if self.shuffle and self.history:
            return self.history.pop()
        if self.current == -1:
            return 0
        return (self.current - 1) % count