class RSData:

    def __init__(self, satellite, sensor, description='temp no'):
        self.satellite = satellite
        self.sensor = sensor
        self.description = description

    def __repr__(self):
        return "satellite={0},sensor={1},description={2}".format(self.satellite, self.sensor, self.description)


