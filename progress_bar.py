import time
import sys

class ProgressBar:
    def __init__(self, toolbar_width = 40):
        self.toolbar_width = toolbar_width
        self.progress = 0
        self.step_width = 1/toolbar_width
        # setup progressbar
        sys.stdout.write("[%s]" % (" " * self.toolbar_width))
        sys.stdout.flush()
        sys.stdout.write("\b" * (self.toolbar_width+1)) # return to start of line, after '['

    def nextTick(self, step = 1):
        # update the bar
        for i_ in range(step):
            sys.stdout.write("-")
            sys.stdout.flush()
    
    def update(self, current, total):
        if current / total > self.progress:
            while (current / total) >= self.progress:
                self.nextTick(step=1)
                self.progress += self.step_width
        pass


    def clean(self):
        sys.stdout.write("\n")

    def __enter__(self):
        return self

    def __exit__(self, a, b, c):
        pass



