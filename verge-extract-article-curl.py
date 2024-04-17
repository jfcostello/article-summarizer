import subprocess

def fetch_content(url):
    # Running the curl command with UTF-8 encoding specified
    result = subprocess.run(['curl', url], capture_output=True, text=True, encoding='utf-8')
    return result.stdout

url = 'https://www.theverge.com/2024/4/14/24130379/google-pixel-9-emergency-satellite-sos-modem-apple-iphone'
content = fetch_content(url)
print(content)