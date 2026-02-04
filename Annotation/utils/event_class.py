

class Event:

	def __init__(self, label=None, half=None, time=None, team=None, position=None, visibility=None, frame=None):

		self.label = label
		self.half = half
		self.time = time
		self.team = team
		self.position = position
		self.visibility = visibility
		self.frame = frame # if frame is not None else 0

	def to_text(self):
		if self.team and self.team != "None":
			label = self.label + " (" + self.team + ")"
		else:
			label = self.label

		return "Frame: " + str(self.frame) + " || " + label + " - " + str(self.half) + " - " + str(self.visibility)

	def __lt__(self, other):
		self.position < other.position

def ms_to_time(position):
	minutes = int(position//1000)//60
	seconds = int(position//1000)%60
	return str(minutes).zfill(2) + ":" + str(seconds).zfill(2)