class Photo:
    def __init__(self, name, width, height, file_bytes):
        self.name = name
        self.width = width
        self.height = height
        self.file_bytes = file_bytes

    def __eq__(self, other):
        if isinstance(other, Photo):
            return self.width * self.height == other.width * other.height

    def __le__(self, other):
        if isinstance(other, Photo):
            return self.width * self.height < other.width * other.height