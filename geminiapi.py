from google import genai

client = genai.Client(api_key="AIzaSyAASvZ6pj_05d0c6-VWJb1P8kqd3exc-Hk")  # pass key directly

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain how AI works in a few words"
)

print(response.text)
