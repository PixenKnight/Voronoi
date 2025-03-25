import time
from queue import PriorityQueue
from random import randint

import pygame


# Function to check if a coordinate is within the canvas
def in_canvas(coordinate):
	return (0 <= coordinate[0] <= w) and (0 <= coordinate[1] <= h)


# Distance functions for calculating distances between points
def distance(p1, p2, func="euclidean"):
	if func == "euclidean":
		return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5
	elif func == "manhattan":
		return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
	elif func == "chebyshev":
		return max(abs(p1[0] - p2[0]), abs(p1[1] - p2[1]))
	elif func == "inv_chebyshev":
		return min(abs(p1[0] - p2[0]), abs(p1[1] - p2[1]))
	else:
		raise ValueError("Invalid distance function")


# Function used to generate random colors. Random samples are kinda ugly but it works.
def generate_colors():
	return randint(100, 255), randint(100, 255), randint(100, 255)


# Parameters
w = 900
h = 900
size = 2

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
marker = (-1,)  # Marks the end of a drawing cycle, put into the queue at each integer radius
max_r = distance((0, 0), (w, h))  # Maximum possible distance
# points = [((randint(50, w - 50), randint(50, h - 50)), generate_colors()) for _ in range(16)]  # Randomly-generated points
points = [(((i // 4) * (w / 4) + (w / 8), (i % 4) * (h / 4) + (h / 8)),
           generate_colors()) for i in range(16)]  # Even grid for benchmarks
queue = PriorityQueue()
for point in points:
	queue.put((0, point[0]))  # Place seed points in queue
queue.put((r, marker))  # First marker
min_point = ((w, h),)  # Initial condition of smallest point
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

			pygame.draw.rect(canvas, min_point[1], (curr[0], curr[1], size, size))

			# Add curr's neighbors to the queue iff:
			#   1. The neighbor is further from the found min_point than curr
			#   2. The neighbor has not been drawn
			#   3. The neighbor is located within the canvas
			# Switching to a function that generates a list of neighbors and then iterating over it caused 3x slowdowns!
			new_point = (curr[0], curr[1] + size)
			new_dst = distance(new_point, min_point[0])
			if min_dst <= new_dst and new_point not in drawn_points and in_canvas(new_point):
				queue.put((new_dst, new_point))
				drawn_points.add(new_point)
			new_point = (curr[0], curr[1] - size)
			new_dst = distance(new_point, min_point[0])
			if min_dst <= new_dst and new_point not in drawn_points and in_canvas(new_point):
				queue.put((new_dst, new_point))
				drawn_points.add(new_point)
			new_point = (curr[0] + size, curr[1])
			new_dst = distance(new_point, min_point[0])
			if min_dst <= new_dst and new_point not in drawn_points and in_canvas(new_point):
				queue.put((new_dst, new_point))
				drawn_points.add(new_point)
			new_point = (curr[0] - size, curr[1])
			new_dst = distance(new_point, min_point[0])
			if min_dst <= new_dst and new_point not in drawn_points and in_canvas(new_point):
				queue.put((new_dst, new_point))
				drawn_points.add(new_point)

			curr = queue.get()[1]  # Get the next coordinate (or marker) in the queue

		r += size  # Expand the radius
		queue.put((r, marker))  # Place a marker at the new radius

		for point in points:
			pygame.draw.circle(canvas, "black", point[0], 3)  # Seed points are drawn over everything else

		pygame.display.flip()
	elif end_time == 0 and running == 1:  # Done drawing, can print benchmark time
		end_time = time.time()
		print("Time taken: ", end_time - start_time)

	if running > 3:  # Stepped through the simulation, revert to paused state
		running = 3

pygame.quit()
