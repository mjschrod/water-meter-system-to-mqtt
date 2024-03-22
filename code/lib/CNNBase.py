import tflite_runtime.interpreter as tflite

from PIL import Image
import numpy as np
from PIL import Image

import os
from shutil import copyfile
import logging

from importlib import util

spam_spec = util.find_spec("tensorflow")
found_tensorflow = spam_spec is not None

spam_spec = util.find_spec("tflite_runtime")
found_tflite = spam_spec is not None

logger = logging.getLogger(__name__)


class CNNBase:
    def __init__(self, in_Modelfile, in_dx, in_dy, in_LogImageLocation):
        self.log_Image = in_LogImageLocation
        self.LogNames = ""
        self.dx = in_dx
        self.dy = in_dy
        self.GlobalError = False
        self.GlobalErrorText = ""
        self.model_file = in_Modelfile

        self.CheckAndLoadDefaultConfig()

    def _LoadModel(self):
        filename, file_extension = os.path.splitext(self.model_file)
        if file_extension != ".tflite":
            logger.error(
                "Only TFLite-Model (*.tflite) are support since version 7.0.0 and higher"
            )
            self.GlobalError = True
            self.GlobalErrorText = "AnalogCNN-File for Analog Neural Network is not tflite-Format. If you want to use h5-files you need to downgrade to v6.1.1. This is not recommended."
            return

        self.interpreter = tflite.Interpreter(model_path=self.model_file)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def Readout(self, PictureList, logtime):
        self.result = []
        for image in PictureList:
            value = self.ReadoutSingleImage(image[1])
            if len(self.log_Image) > 0:
                self.saveLogImage(image, value, logtime)
            self.result.append(value)
        return self.result

    def CheckAndLoadDefaultConfig(self):
        defaultdir = "./config_default/"
        targetdir = "./config/"
        if not os.path.exists(self.model_file):
            zerlegt = self.model_file.split("/")
            pfad = zerlegt[0]
            for i in range(1, len(zerlegt) - 1):
                pfad = pfad + "/" + zerlegt[i]
                if not os.path.exists(pfad):
                    os.makedirs(pfad)
            defaultmodel = self.model_file.replace(targetdir, defaultdir)
            copyfile(defaultmodel, self.model_file)
        if len(self.log_Image) > 0 and not os.path.exists(self.log_Image):
            zerlegt = self.log_Image.split("/")
            pfad = zerlegt[0]
            for i in range(1, len(zerlegt)):
                pfad = pfad + "/" + zerlegt[i]
                if not os.path.exists(pfad):
                    os.makedirs(pfad)

    def saveLogImage(self, image, value, logtime):
        if (len(self.LogNames) > 0) and (image[0] not in self.LogNames):
            return
        speichername = "{:.1f}".format(value) + "_" + image[0] + "_" + logtime + ".jpg"
        speichername = f"{self.log_Image}/{speichername}"
        image[1].save(speichername, "JPEG")

    def ReadoutSingleImage(self, image):
        logger.debug("Validity 01")
        test_image = image.resize((self.dx, self.dy), Image.NEAREST)
        logger.debug("Validity 02")
        test_image.save("./image_tmp/resize.jpg", "JPEG")
        logger.debug("Validity 03")
        test_image = np.array(test_image, dtype="float32")
        logger.debug("Validity 04")
        img = np.reshape(test_image, [1, self.dy, self.dx, 3])
        logger.debug("Validity 05")

        input_data = img
        self.interpreter.set_tensor(self.input_details[0]["index"], input_data)
        self.interpreter.invoke()
        return self.interpreter.get_tensor(self.output_details[0]["index"])
