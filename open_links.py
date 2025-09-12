import webbrowser

urls = [
    "https://www.linkedin.com/in/scierka",
    "https://www.scierkalang.com", 
    "https://www.linkedin.com/company/scierka-lang-media",
    "https://twitter.com/ScierkaLang",
    "https://www.facebook.com/ScierkaMedia"
]

for url in urls:
    webbrowser.open(url)
    print(f"Opening: {url}")