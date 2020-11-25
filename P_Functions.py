class P_MinMaxScaler:

    def __init__(self, items):
        self.input = items
        self.minimum = min(items)
        self.maximum = max(items)
        self.scale = self.maximum - self.minimum

    def transform(self):
        output = [P_map(x, self.minimum, self.maximum, 0, 1) for x in self.input]
        return output

    def reverse_transform(self, values):
        output = [P_map(x, 0, 1, self.minimum, self.maximum) for x in values]
        return output


def P_constrain(val, lowerLimit=0, upperLimit=1):
    if val < lowerLimit:
        return lowerLimit
    elif val > upperLimit:
        return upperLimit
    else:
        return val


def P_map(val, lowerLimit, upperLimit, newLowerLimit, newUpperLimit):
    temp_val = val - lowerLimit
    temp_scale = temp_val / (upperLimit - lowerLimit)
    temp_output = ((newUpperLimit - newLowerLimit) * temp_scale) + newLowerLimit
    return temp_output
