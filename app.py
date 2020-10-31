# import the necessary packages
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
import numpy as np
import cv2
import os
import time
import shutil
import streamlit as st
from PIL import Image
from pathlib import Path

def local_css(file_name):
	with open(Path(file_name)) as f:
		st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
local_css("./assets/style.css")

st.markdown("<h1 style='text-align: center ; color: black;'>Detecção de Máscara 😷</h1>", unsafe_allow_html=True)
st.markdown("<h6 style='text-align: center ; color: black;'>Trabalho desenvolvido para a disciplina de Projetos de Sistemas de Informação.</h6>", unsafe_allow_html=True)

#st.sidebar.header("Mask Detection Confidence")
min_confidence = 0.5

uploaded_file = st.file_uploader("Faça o upload de uma imagem")

if uploaded_file is not None:
	image = None
	# Convert the file to an opencv image.
	file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
	image = cv2.imdecode(file_bytes, 1)

	gif_path = './assets/giphy.gif'
	gif_runner = st.image(gif_path)
	# load our serialized face detector model from disk
	#print("[INFO] loading face detector model...")
	mask_detector_model = os.path.sep.join(["mask_detector", "mask_detector.model"])
	prototxtPath = os.path.sep.join(["face_detector", "deploy.prototxt"])
	weightsPath = os.path.sep.join(["face_detector", "res10_300x300_ssd_iter_140000.caffemodel"])
	net = cv2.dnn.readNet(prototxtPath, weightsPath)
	# load the face mask detector model from disk
	model = load_model(mask_detector_model)
	# load the input image from disk, clone it, and grab the image spatial
	# dimensions
	orig = image.copy()
	(h, w) = image.shape[:2]
	# construct a blob from the image
	blob = cv2.dnn.blobFromImage(image, 1.0, (300, 300),
		(104.0, 177.0, 123.0))

	# pass the blob through the network and obtain the face detections
	net.setInput(blob)
	detections = net.forward()

	# loop over the detections
	for i in range(0, detections.shape[2]):
		# extract the confidence (i.e., probability) associated with
		# the detection
		confidence = detections[0, 0, i, 2]

		# filter out weak detections by ensuring the confidence is
		# greater than the minimum confidence
		if confidence > min_confidence:
			# compute the (x, y)-coordinates of the bounding box for
			# the object
			box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
			(startX, startY, endX, endY) = box.astype("int")

			# ensure the bounding boxes fall within the dimensions of
			# the frame
			(startX, startY) = (max(0, startX), max(0, startY))
			(endX, endY) = (min(w - 1, endX), min(h - 1, endY))

			# extract the face ROI, convert it from BGR to RGB channel
			# ordering, resize it to 224x224, and preprocess it
			face = image[startY:endY, startX:endX]
			face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
			face = cv2.resize(face, (224, 224))
			face = img_to_array(face)
			face = preprocess_input(face)
			face = np.expand_dims(face, axis=0)

			# pass the face through the model to determine if the face
			# has a mask or not
			(mask, withoutMask) = model.predict(face)[0]

			# determine the class label and color we'll use to draw
			# the bounding box and text
			label = "Mask" if mask > withoutMask else "No Mask"
			color = (0, 255, 0) if label == "Mask" else (0, 0, 255)

			# include the probability in the label
			label = "{}: {:.2f}%".format(label, max(mask, withoutMask) * 100)

			# display the label and bounding box rectangle on the output
			# frame
			cv2.putText(image, label, (startX, startY - 10),
				cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
			cv2.rectangle(image, (startX, startY), (endX, endY), color, 2)

	folder_name = "output"
	if not os.path.exists(folder_name):
		os.mkdir(folder_name)

	output_image = os.path.join(folder_name, uploaded_file.name)
	cv2.imwrite(output_image, image)

	gif_runner.empty()
		
	st.image(output_image)

	try:
		shutil.rmtree('output')
	except OSError as e:
		st.write("Error: %s - %s." % (e.filename, e.strerror))
