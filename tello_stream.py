import ffmpeg
import cv2
import numpy as np

TELLO_ENDPOINT = 'udp://192.168.10.1:11111'
IMG_W = 960
IMG_H = 720
IMG_C = 3

def start_stream():
	process1 = (
		ffmpeg
		.input(TELLO_ENDPOINT)
		.output('pipe:', format='rawvideo', pix_fmt='rgb24')
		.run_async(pipe_stdout=True)
	)
	while True:
		in_bytes = process1.stdout.read(IMG_W * IMG_H * IMG_C)
		if not in_bytes:
			break
		inframe = np.frombuffer(in_bytes, np.uint8)
		inframe = inframe.reshape((IMG_H, IMG_W, IMG_C))
		cv2.imshow('outshow', inframe)

	process1.wait()
	cv2.destroyAllWindows()
