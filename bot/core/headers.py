headers = {
    'Accept-Language': 'en-GB,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Host': 'api.hamsterkombat.io',
    'Origin': 'https://hamsterkombat.io',
    'Referer': 'https://hamsterkombat.io/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
}

additional_headers_for_empty_requests = {
    'Accept': '*/*',
    'Content-Length': "0",
}

def createAdditionalHeadersForDataRequests(content_length: int) -> dict:
    return {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Content-Length': str(content_length),
    }