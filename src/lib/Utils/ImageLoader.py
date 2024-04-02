import time
import logging
import requests

logger = logging.getLogger(__name__)


class DownloadFailure(Exception):
    ...
    pass


def loadImageFromUrl(url: str, timeout: int = 10, minImageSize: int = 0) -> bytes:
    try:
        startTime = time.time()
        data = _readImageFromUrl(url, timeout)
        size = len(data)
        if size < minImageSize:
            raise DownloadFailure(
                f"Imagefile too small. Size {size}, min size is {minImageSize}, "
                f"url: {url}"
            )
        return data
    except Exception as e:
        raise DownloadFailure(f"Image download failure from {url}: {str(e)}") from e
    finally:
        logger.debug(f"Image downloaded in {time.time() - startTime:.3f} sec")


def _readImageFromUrl(url: str, timeout: int) -> None:
    # Todo: limit file to one folder for security reasons
    if url.startswith("file://"):
        file = url[7:]
        with open(file, "rb") as f:
            return f.read()
    else:
        data = requests.get(url, timeout=timeout)
        return data.content