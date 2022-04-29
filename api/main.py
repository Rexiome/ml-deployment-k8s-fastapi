"""
Adapted from:

(1) https://github.com/shanesoh/deploy-ml-fastapi-redis-docker/
(2) https://github.com/aniketmaurya/tensorflow-fastapi-starter-pack
"""

import json
import urllib.request

import onnxruntime as ort
from fastapi import FastAPI, File, Form, HTTPException
from typing import Optional
from utils import decode_predictions, prepare_image


app = FastAPI(title="ONNX image classification API")


@app.get("/")
async def home():
    return "Welcome!"


@app.on_event("startup")
def load_modules():
    model_filename = "resnet50_w_preprocessing.onnx"
    model_url = f"https://github.com/sayakpaul/ml-deployment-k8s-fastapi/releases/download/v1.0.0/{model_filename}"
    urllib.request.urlretrieve(model_url, model_filename)

    global resnet_model_sess
    resnet_model_sess = ort.InferenceSession(model_filename)

    category_filename = "imagenet_classes.txt"
    category_url = (
        f"https://raw.githubusercontent.com/pytorch/hub/master/{category_filename}"
    )
    urllib.request.urlretrieve(category_url, category_filename)

    global imagenet_categories
    with open(category_filename, "r") as f:
        imagenet_categories = [s.strip() for s in f.readlines()]    


 @app.post("/predict/image")
 async def predict_api(image_file: bytes = File(...), with_resize: bool = Form(...), with_post_process: bool = Form(...)):
     image = prepare_image(image_file, with_resize)

     if len(image.shape) != 4:
         raise HTTPException(
             status_code=400, detail="Only 3-channel RGB images are supported."
         )

     predictions = resnet_model_sess.run(None, {"image_input": image})[0]
     if with_post_process:
        response_dict = decode_predictions(predictions, imagenet_categories)
        return json.dumps(response_dict)
     else:
         return "OK"

     
