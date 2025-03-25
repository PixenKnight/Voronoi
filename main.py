import math
import time
from queue import PriorityQueue
from random import randint

import pygame

# Parameters
w = 900
h = 900
size = 2
seeds = 16


class Point:
	"""
	Point class used to represent x-y coordinates
	"""
	def __init__(self, x, y):
		self.x = x
		self.y = y
		self.magnitude = self.x + self.y

	def to_tuple(self) -> tuple[int, int]:
		return self.x, self.y

	def __repr__(self) -> str:
		return f"Point({self.x}, {self.y})"

	def __lt__(self, other: 'Point') -> bool:
		return self.magnitude < other.magnitude

	def __hash__(self) -> int:
		return hash(self.to_tuple())

	def __eq__(self, other: 'Point') -> bool:
		return self.x == other.x and self.y == other.y


# Function to check if a coordinate is within the canvas
def in_canvas(coordinate: Point):
	return (0 <= coordinate.x <= w) and (0 <= coordinate.y <= h)


# Distance functions for calculating distances between points
def distance(p1: Point, p2: Point, func="euclidean"):
	if func == "euclidean":
		return ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
	elif func == "manhattan":
		return abs(p1.x - p2.x) + abs(p1.y - p2.y)
	elif func == "chebyshev":
		return max(abs(p1.x - p2.x), abs(p1.y - p2.y))
	elif func == "inv_chebyshev":
		return min(abs(p1.x - p2.x), abs(p1.y - p2.y))
	else:
		raise ValueError("Invalid distance function")


# Function used to generate random colors. Random samples are kinda ugly but it works.
def generate_color() -> tuple[int, int, int]:
	return randint(100, 255), randint(100, 255), randint(100, 255)


def generate_points(uniform: bool = False) -> tuple[Point, tuple[int, int, int]]:
	seed_sqrt = math.floor(seeds ** 0.5)
	for i in range(seeds):
		if uniform:
			yield Point((i // seed_sqrt) * (w / seed_sqrt) + (w / (seed_sqrt * 2)),
			            (i % seed_sqrt) * (h / seed_sqrt) + (h / (seed_sqrt * 2))),(generate_color())
		else:
			yield Point(randint(50, w - 50), randint(50, h - 50)), (generate_color())


# Pygame initialization
pygame.init()
canvas = pygame.display.set_mode((w, h), vsync=True)

# Benchmark timers
end_time = 0
start_time = time.time()

# Setup for queue and main loop
#   The queue is a PriorityQueue, where the priority number is equal to an increasing radius.
#   This allows all pixels below said radius to be popped before flipping the screen.
running = 2  # States for the loop, 0 == exit, 1 == done drawing, 2 == running, 3 == paused, 4 == stepping while paused
r = size * 2
marker = Point(-1, -1)  # Marks the end of a drawing cycle, put into the queue at each integer radius
max_r = distance(Point(0, 0), Point(w, h))  # Maximum possible distance
points: list[tuple[Point, tuple[int, int, int]]] = [(point, color) for (point, color) in generate_points(True)]  # Generate seed points
queue = PriorityQueue()
for point in points:
	queue.put((0, point[0]))  # Place seed points in queue
queue.put((r, marker))  # First marker
min_point = (Point(w, h),(0,0,0))  # Initial condition of smallest point
drawn_points = set([point[0] for point in points])  # Keep track of drawn points to prevent redrawing

canvas.fill("white")

while running > 0:
	for event in pygame.event.get():
		if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):  # Quit
			running = 0
		elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:  # Pause/resume the sim
			if running == 3:
				running = 2
			elif running == 2:
				running = 3
		elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT and running == 3:  # Step while paused
			running = 4

	if running == 2 or running == 4:  # Running or stepping
		curr = queue.get()[1]
		if curr == marker:  # Only markers at this point, done drawing
			running = 1
		while curr != marker:  # Points remaining to be drawn at this radius
			min_dst = max_r
			for point in points:
				dst = distance(point[0], curr)
				if dst < min_dst:  # Get the closest point to this curr location
					min_dst = dst
					min_point = point

			pygame.draw.rect(canvas, min_point[1], (curr.x, curr.y, size, size))

			# Add curr's neighbors to the queue iff:
			#   1. The neighbor is further from the found min_point than curr
			#   2. The neighbor has not been drawn
			#   3. The neighbor is located within the canvas
			# Switching to a function that generates a list of neighbors and then iterating over it caused 3x slowdowns!
			new_point = Point(curr.x, curr.y + size)
			new_dst = distance(new_point, min_point[0])
			if min_dst <= new_dst and new_point not in drawn_points and in_canvas(new_point):
				queue.put((new_dst, new_point))
				drawn_points.add(new_point)
			new_point = Point(curr.x, curr.y - size)
			new_dst = distance(new_point, min_point[0])
			if min_dst <= new_dst and new_point not in drawn_points and in_canvas(new_point):
				queue.put((new_dst, new_point))
				drawn_points.add(new_point)
			new_point = Point(curr.x + size, curr.y)
			new_dst = distance(new_point, min_point[0])
			if min_dst <= new_dst and new_point not in drawn_points and in_canvas(new_point):
				queue.put((new_dst, new_point))
				drawn_points.add(new_point)
			new_point = Point(curr.x - size, curr.y)
			new_dst = distance(new_point, min_point[0])
			if min_dst <= new_dst and new_point not in drawn_points and in_canvas(new_point):
				queue.put((new_dst, new_point))
				drawn_points.add(new_point)

			curr = queue.get()[1]  # Get the next coordinate (or marker) in the queue

		r += size  # Expand the radius
		queue.put((r, marker))  # Place a marker at the new radius

		for point in points:
			pygame.draw.circle(canvas, "black", point[0].to_tuple(), 3)  # Seed points are drawn over everything else

		pygame.display.flip()
	elif end_time == 0 and running == 1:  # Done drawing, can print benchmark time
		end_time = time.time()
		print("Time taken: ", end_time - start_time)

	if running > 3:  # Stepped through the simulation, revert to paused state
		running = 3

pygame.quit()
