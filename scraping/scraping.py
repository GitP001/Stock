import http.client, urllib.parse

conn = http.client.HTTPSConnection('api.marketaux.com')

params = urllib.parse.urlencode({
    'api_token': 'UjLiUOQxiMYzxoyPx5Apc2qbQVwz3xKMcMtPZJ9q',
    'symbols': 'AAPL,TSLA',
    'limit': 50,
    })

conn.request('GET', '/v1/news/all?{}'.format(params))

res = conn.getresponse()
data = res.read()

print(data.decode('utf-8'))
