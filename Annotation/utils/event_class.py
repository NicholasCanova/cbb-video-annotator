

class Event:

	def __init__(self, label=None, half=None, time=None, subType=None, position=None, visibility=None, frame=None, fourthType=None):

		self.label = label
		self.half = half
		self.time = time
		self.subType = subType
		self.position = position
		self.visibility = visibility
		self.frame = frame # if frame is not None else 0
		self.fourthType = fourthType

	def to_text(self):
		if self.subType and self.subType != "None":
			label = self.label + " (" + self.subType + ")"
		else:
			label = self.label

		parts = [f"Frame: {self.frame}", label, str(self.half)]

		if self.visibility and self.visibility != "None":
			parts.append(str(self.visibility))

		if self.fourthType and self.fourthType != "None":
			parts.append(str(self.fourthType))

		return " || ".join([parts[0], " - ".join(parts[1:])])

	def __lt__(self, other):
		self.position < other.position

def ms_to_time(position):
	minutes = int(position//1000)//60
	seconds = int(position//1000)%60
	return str(minutes).zfill(2) + ":" + str(seconds).zfill(2)