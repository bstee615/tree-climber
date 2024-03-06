class Counter:
    def __init__(self):
        self._id = 0
    
    def get(self):
        return self._id
    
    def get_and_increment(self):
        _id = self.get()
        self._id += 1
        return _id
