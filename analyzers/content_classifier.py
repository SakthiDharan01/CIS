import magic
import mimetypes
from urllib.parse import urlparse

class ContentClassifier:
    """
    Content Type Classification Engine
    - MIME type detection
    - Basic file signature via python-magic
    - URL format validation
    """

    def classify_file(self, file_path: str):
        mime = magic.Magic(mime=True)
        content_type = mime.from_file(file_path)
        guess = mimetypes.guess_type(file_path)[0]
        fmt = None

        if guess:
            fmt = guess.split('/')[-1]
        if '/' in content_type:
            fmt = content_type.split('/')[-1]

        return {
            "content_type": content_type.split('/')[0] if '/' in content_type else content_type,
            "format": fmt or "unknown",
            "raw_mime": content_type
        }

    def classify_url(self, url: str):
        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc:
            return {
                "content_type": "url",
                "format": parsed.scheme,
                "raw_mime": "text/html"
            }
        return {
            "content_type": "unknown",
            "format": None,
            "raw_mime": None
        }
