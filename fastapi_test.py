import requests

response = requests.post(
    "http://40.82.143.107:8000/search",
    json={
        "query": "자세한 통계 보기를 누르면 오류가 나는데 어떻게 고쳐?",
        "k": 5,
        "rerank": True
    }
)

print(response.json())