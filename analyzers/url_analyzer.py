import requests
from urllib.parse import urlparse
import socket
import ssl
import datetime
from bs4 import BeautifulSoup
import statistics


class URLAnalyzer:
    def analyze(self, url):
        details = []
        score = 100

        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc

            details.append(f"Domain: {domain}")

            # 1. SSL Check
            try:
                ctx = ssl.create_default_context()
                with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
                    s.settimeout(5)
                    s.connect((domain, 443))
                    cert = s.getpeercert()
                    not_after = datetime.datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_left = (not_after - datetime.datetime.utcnow()).days
                    details.append(f"SSL expires in {days_left} days")
                    if days_left < 0:
                        score -= 40
                        details.append("SSL certificate expired.")
            except Exception as e:
                score -= 20
                details.append(f"SSL Error: {str(e)}")

            # 2. Content Analysis (HTML structure + linguistics)
            try:
                response = requests.get(url, timeout=8, allow_redirects=True)
                if response.history:
                    score -= 5
                    details.append(f"Redirect chain length: {len(response.history)}")
                if response.status_code == 200:
                    html_content = response.text
                    soup = BeautifulSoup(html_content, 'html.parser')

                    # Tag repetition (structure uniformity)
                    tags = [tag.name for tag in soup.find_all()]
                    if tags:
                        most_common = max(set(tags), key=tags.count)
                        freq = tags.count(most_common) / max(1, len(tags))
                        details.append(f"Most common tag '{most_common}' ratio: {freq:.2f}")
                        if freq > 0.35:
                            score -= 10
                            details.append("DOM heavily repetitive (auto-generated suspicion).")

                    # Sentence length uniformity
                    text = soup.get_text(separator=" ")
                    sentences = [s.strip() for s in text.split('.') if s.strip()]
                    if sentences:
                        lengths = [len(s.split()) for s in sentences if len(s.split()) > 0]
                        if lengths:
                            mean_len = statistics.mean(lengths)
                            std_len = statistics.pstdev(lengths)
                            details.append(f"Sentence length mean/std: {mean_len:.1f}/{std_len:.1f}")
                            if std_len < 3:
                                score -= 10
                                details.append("Highly uniform sentence lengths (AI-like formatting).")

                    # Keyword over-optimization
                    words = [w.lower() for w in text.split()]
                    if words:
                        top_word = max(set(words), key=words.count)
                        ratio = words.count(top_word) / max(1, len(words))
                        details.append(f"Top word '{top_word}' ratio: {ratio:.3f}")
                        if ratio > 0.05:
                            score -= 5
                            details.append("Keyword repetition is high (over-optimized content).")

                    if "generator" in html_content.lower() and "ai" in html_content.lower():
                        score -= 20
                        details.append("'AI' mentioned in generator meta tag.")
                else:
                    score -= 10
                    details.append(f"URL status code: {response.status_code}")
            except Exception as e:
                score -= 10
                details.append(f"Could not fetch URL content: {str(e)}")

        except Exception as e:
            details.append(f"Error in URL analysis: {str(e)}")
            score -= 10

        return {
            "layer": "Content-Specific AI Pattern Integrity (URL)",
            "score": max(0, score),
            "details": details
        }
