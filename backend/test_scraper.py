import httpx
from bs4 import BeautifulSoup

# Fetch a small department
url = "https://app.testudo.umd.edu/soc/202501/CMSC"

response = httpx.get(url, timeout=30.0)
soup = BeautifulSoup(response.text, 'html.parser')

# Save HTML for inspection
with open('sample_page.html', 'w', encoding='utf-8') as f:
    f.write(response.text)

print("HTML saved to sample_page.html")
print(f"Status: {response.status_code}")
print(f"Length: {len(response.text)} chars")

# Try to find course containers with different selectors
print("\n=== Looking for course elements ===")
print(f"divs with 'course': {len(soup.find_all('div', class_='course'))}")
print(f"divs with 'course-id': {len(soup.find_all('div', class_='course-id'))}")
print(f"any 'course' in class: {len(soup.find_all(class_=lambda x: x and 'course' in x))}")

# Check for any div/span IDs
print("\n=== Sample IDs ===")
for elem in soup.find_all(id=True)[:10]:
    print(f"{elem.name}: id='{elem.get('id')}'")

# Check for common data attributes
print("\n=== Sample data attributes ===")
for elem in soup.find_all(attrs={'data-course': True})[:5]:
    print(f"data-course: {elem.get('data-course')}")
