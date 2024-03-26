import json
import signal
from lib.LoadImageFile import DownloadFailure
from lib.MeterValue import MeterValue
import os
import gc
import logging
import sys
from fastapi import FastAPI, Response, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

version = "Version 8.0.0 (2024-03-22)"
watermeter = None

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = FastAPI(title="Watermeter")
app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")


@app.get("/", response_class=HTMLResponse)
def getIndex(request: Request):
    return templates.TemplateResponse(
        "index.html", context={"request": request, "version": version}
    )


@app.get("/healthcheck")
def healthcheck():
    return "Health - OK"


@app.get("/image_tmp/{image}")
def getImage(image: str):
    return FileResponse(
        f"{imageTmpFolder}/{image}", media_type="image/jpg", filename=image
    )


@app.get("/version", response_class=HTMLResponse)
def getVersion():
    return version


@app.get("/exit", response_class=HTMLResponse)
def doExit():
    os.kill(os.getpid(), signal.SIGTERM)
    return "App will exit in immidiately"


@app.get("/reload", response_class=HTMLResponse)
def reloadConfig():
    global watermeter
    del watermeter
    gc.collect()
    watermeter = MeterValue(
        configFile=f"{configDir}/config.ini",
        prevValueFile=f"{configDir}/prevalue.ini",
        imageTmpFolder=imageTmpFolder,
    )
    return "Configuration reloaded"


@app.get("/roi", response_class=HTMLResponse)
def getRoi(request: Request, url: str = "", timeout: int = 0):
    try:
        watermeter.getROI(url, timeout)
        return templates.TemplateResponse(
            "roi.html",
            context={"request": request, "image": "/image_tmp/roi.jpg"},
        )
    except DownloadFailure as e:
        return f"Error: {e}"


@app.get("/setPreValue", response_class=HTMLResponse)
def setPreValue(value: float):
    return watermeter.setPreValue(value)


@app.get("/watermeter")
def getMeterValue(
    format: str = "html",
    url: str = "",
    simple: bool = True,
    usePreValue: bool = False,
    single: bool = False,
    ignoreConsistencyCheck: bool = False,
    timeout: int = 0,
):
    if format == "json":
        result = watermeter.getMeterValueJson(
            url=url,
            simple=simple,
            usePreValue=usePreValue,
            single=single,
            ignoreConsistencyCheck=ignoreConsistencyCheck,
            timeout=timeout,
        )

        return Response(
            json.dumps(result),
            media_type="application/json",
        )
    else:
        result = watermeter.getMeterValueHtml(
            url=url,
            simple=simple,
            usePreValue=usePreValue,
            single=single,
            ignoreConsistencyCheck=ignoreConsistencyCheck,
            timeout=timeout,
        )

        return Response(
            result,
            media_type="text/html",
        )


if __name__ == "__main__":
    logLevel = os.environ.get("LOG_LEVEL")
    if logLevel is not None:
        logger.setLevel(logLevel)

    logging.getLogger("lib.CNNBase").setLevel(logger.level)
    logging.getLogger("lib.CutImage").setLevel(logger.level)
    logging.getLogger("lib.LoadFileFromHTTP").setLevel(logger.level)
    logging.getLogger("lib.Config").setLevel(logger.level)
    logging.getLogger("lib.AnalogCounterCNN").setLevel(logger.level)
    logging.getLogger("lib.DigitalCounterCNN").setLevel(logger.level)
    logging.getLogger("lib.MeterValue").setLevel(logger.level)

    configDir = os.environ.get("CONFIG_DIR", "/config")
    imageTmpFolder = os.environ.get("IMAGE_TMP", "/image_tmp")
    watermeter = MeterValue(
        configFile=f"{configDir}/config.ini",
        prevValueFile=f"{configDir}/prevalue.ini",
        imageTmpFolder=imageTmpFolder,
    )

    port = 3000
    logger.info(f"Watermeter is serving at port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
