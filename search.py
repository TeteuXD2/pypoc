import sys
import subprocess
import requests
import csv  # Alternative to pandas
import argparse
import time
import os
from bs4 import BeautifulSoup

# Verify Python version
required_version = (3, 12, 7)
if sys.version_info < required_version:
    print(f"Error: This script requires Python {'.'.join(map(str, required_version))} or higher.")
    sys.exit(1)

# Function to install requirements
def install_requirements():
    with open('requirements.txt') as f:
        packages = f.readlines()
    
    packages = [pkg.strip() for pkg in packages if pkg.strip()]
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', *packages])

# Install requirements if needed
install_requirements()

# Function to save results
def save_results(results, output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'url', 'snippet']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for result in results:
            writer.writerow(result)

# Define search functions
def search_bing(api_key, query, file_type=None, limit=10, timeout=10, user_agent=None, verify_ssl=True):
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    if user_agent:
        headers['User-Agent'] = user_agent
    params = {
        "q": query,
        "count": limit,
        "responseFilter": "webpages"
    }

    if file_type:
        params["q"] += f" filetype:{file_type}"

    results = []
    url = "https://api.bing.microsoft.com/v7.0/search"

    try:
        response = requests.get(url, headers=headers, params=params, timeout=timeout, verify=verify_ssl, stream=True)
        response.raise_for_status()
        
        # Decode response content if needed
        if response.headers.get('Content-Encoding') == 'br':
            content = response.content.decode('utf-8')
        else:
            content = response.text

        data = response.json()

        for item in data.get("webPages", {}).get("value", []):
            results.append({
                "name": item["name"],
                "url": item["url"],
                "snippet": item["snippet"]
            })

    except requests.exceptions.Timeout:
        print("Request timed out.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    return results

def search_google(query, file_type=None, limit=10, timeout=10, user_agent=None, verify_ssl=True):
    results = []
    google_search_url = "https://www.google.com/search"
    headers = {'User-Agent': user_agent} if user_agent else {}
    params = {"q": query, "num": limit}

    if file_type:
        params["q"] += f" filetype:{file_type}"

    try:
        response = requests.get(google_search_url, headers=headers, params=params, timeout=timeout, verify=verify_ssl, stream=True)
        response.raise_for_status()
        
        # Decode response content if needed
        if response.headers.get('Content-Encoding') == 'br':
            content = response.content.decode('utf-8')
        else:
            content = response.text

        soup = BeautifulSoup(content, 'html.parser')

        for item in soup.find_all('h3'):
            a_tag = item.find_parent('a')
            if a_tag:
                results.append({
                    "name": item.get_text(),
                    "url": a_tag['href'],
                    "snippet": ''  # Google doesn't provide snippets easily
                })

        time.sleep(1)  # Delay to control request speed

    except requests.exceptions.Timeout:
        print("Request timed out.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    return results

def search_duckduckgo(query, file_type=None, limit=10, timeout=10, user_agent=None, verify_ssl=True):
    results = []
    ddg_search_url = "https://duckduckgo.com/"
    headers = {'User-Agent': user_agent} if user_agent else {}
    params = {"q": query, "t": "h_"}

    if file_type:
        params["q"] += f" filetype:{file_type}"

    try:
        response = requests.get(ddg_search_url, headers=headers, params=params, timeout=timeout, verify=verify_ssl, stream=True)
        response.raise_for_status()
        
        # Decode response content if needed
        if response.headers.get('Content-Encoding') == 'br':
            content = response.content.decode('utf-8')
        else:
            content = response.text

        soup = BeautifulSoup(content, 'html.parser')

        for item in soup.find_all('a', class_='result__a'):
            results.append({
                "name": item.get_text(),
                "url": item['href'],
                "snippet": ''  # DuckDuckGo doesn't provide snippets easily
            })

        time.sleep(1)  # Delay to control request speed

    except requests.exceptions.Timeout:
        print("Request timed out.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    return results

# New search functions for additional engines
def search_yandex(api_key, query, file_type=None, limit=10, timeout=10, user_agent=None, verify_ssl=True):
    headers = {'Authorization': f'Api-Key {api_key}'}
    if user_agent:
        headers['User-Agent'] = user_agent
    params = {
        "text": query,
        "count": limit,
        "type": "all"
    }

    if file_type:
        params["text"] += f" filetype:{file_type}"

    results = []
    url = "https://yandex.com/search/xml"

    try:
        response = requests.get(url, headers=headers, params=params, timeout=timeout, verify=verify_ssl, stream=True)
        response.raise_for_status()
        
        # Decode response content if needed
        if response.headers.get('Content-Encoding') == 'br':
            content = response.content.decode('utf-8')
        else:
            content = response.text

        data = response.json()

        for item in data.get("results", []):
            results.append({
                "name": item.get("title"),
                "url": item.get("url"),
                "snippet": item.get("snippet")
            })

    except requests.exceptions.Timeout:
        print("Request timed out.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    return results

def search_yahoo(api_key, query, file_type=None, limit=10, timeout=10, user_agent=None, verify_ssl=True):
    headers = {'Authorization': f'Bearer {api_key}'}
    if user_agent:
        headers['User-Agent'] = user_agent
    params = {
        "q": query,
        "count": limit,
        "format": "json"
    }

    if file_type:
        params["q"] += f" filetype:{file_type}"

    results = []
    url = "https://search.yahoo.com/search"

    try:
        response = requests.get(url, headers=headers, params=params, timeout=timeout, verify=verify_ssl, stream=True)
        response.raise_for_status()
        
        # Decode response content if needed
        if response.headers.get('Content-Encoding') == 'br':
            content = response.content.decode('utf-8')
        else:
            content = response.text

        data = response.json()

        for item in data.get("webPages", {}).get("value", []):
            results.append({
                "name": item.get("name"),
                "url": item.get("url"),
                "snippet": item.get("snippet")
            })

    except requests.exceptions.Timeout:
        print("Request timed out.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    return results

def search_ecosia(query, file_type=None, limit=10, timeout=10, user_agent=None, verify_ssl=True):
    results = []
    ecosia_search_url = "https://www.ecosia.org/search"
    headers = {'User-Agent': user_agent} if user_agent else {}
    params = {"q": query}

    if file_type:
        params["q"] += f" filetype:{file_type}"

    try:
        response = requests.get(ecosia_search_url, headers=headers, params=params, timeout=timeout, verify=verify_ssl, stream=True)
        response.raise_for_status()
        
        # Decode response content if needed
        if response.headers.get('Content-Encoding') == 'br':
            content = response.content.decode('utf-8')
        else:
            content = response.text

        soup = BeautifulSoup(content, 'html.parser')

        for item in soup.find_all('a', class_='result'):
            results.append({
                "name": item.get_text(),
                "url": item['href'],
                "snippet": ''  # Ecosia doesn't provide snippets easily
            })

        time.sleep(1)  # Delay to control request speed

    except requests.exceptions.Timeout:
        print("Request timed out.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    return results

def search_brave(query, file_type=None, limit=10, timeout=10, user_agent=None, verify_ssl=True):
    results = []
    brave_search_url = "https://search.brave.com/search"
    headers = {'User-Agent': user_agent} if user_agent else {}
    params = {"q": query}

    if file_type:
        params["q"] += f" filetype:{file_type}"

    try:
        response = requests.get(brave_search_url, headers=headers, params=params, timeout=timeout, verify=verify_ssl, stream=True)
        response.raise_for_status()
        
        # Decode response content if needed
        if response.headers.get('Content-Encoding') == 'br':
            content = response.content.decode('utf-8')
        else:
            content = response.text

        soup = BeautifulSoup(content, 'html.parser')

        for item in soup.find_all('a', class_='result'):
            results.append({
                "name": item.get_text(),
                "url": item['href'],
                "snippet": ''  # Brave doesn't provide snippets easily
            })

        time.sleep(1)  # Delay to control request speed

    except requests.exceptions.Timeout:
        print("Request timed out.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    return results

def search_searx(query, file_type=None, limit=10, timeout=10, user_agent=None, verify_ssl=True):
    results = []
    searx_search_url = "https://searx.org/search"
    headers = {'User-Agent': user_agent} if user_agent else {}
    params = {"q": query, "format": "json"}

    if file_type:
        params["q"] += f" filetype:{file_type}"

    try:
        response = requests.get(searx_search_url, headers=headers, params=params, timeout=timeout, verify=verify_ssl, stream=True)
        response.raise_for_status()
        
        # Decode response content if needed
        if response.headers.get('Content-Encoding') == 'br':
            content = response.content.decode('utf-8')
        else:
            content = response.text

        data = response.json()

        for item in data.get("results", []):
            results.append({
                "name": item.get("title"),
                "url": item.get("url"),
                "snippet": item.get("content")
            })

    except requests.exceptions.Timeout:
        print("Request timed out.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    return results

def search_mojeek(query, file_type=None, limit=10, timeout=10, user_agent=None, verify_ssl=True):
    results = []
    mojeek_search_url = "https://www.mojeek.com/search"
    headers = {'User-Agent': user_agent} if user_agent else {}
    params = {"q": query}

    if file_type:
        params["q"] += f" filetype:{file_type}"

    try:
        response = requests.get(mojeek_search_url, headers=headers, params=params, timeout=timeout, verify=verify_ssl, stream=True)
        response.raise_for_status()
        
        # Decode response content if needed
        if response.headers.get('Content-Encoding') == 'br':
            content = response.content.decode('utf-8')
        else:
            content = response.text

        soup = BeautifulSoup(content, 'html.parser')

        for item in soup.find_all('a', class_='result'):
            results.append({
                "name": item.get_text(),
                "url": item['href'],
                "snippet": ''  # Mojeek doesn't provide snippets easily
            })

        time.sleep(1)  # Delay to control request speed

    except requests.exceptions.Timeout:
        print("Request timed out.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    return results

# Main function to handle command line arguments and initiate search
def main():
    parser = argparse.ArgumentParser(description="Search multiple engines.")
    parser.add_argument('--query', required=True, help='Search query')
    parser.add_argument('--api', nargs='+', choices=['bing', 'google', 'duckduckgo', 'yandex', 'yahoo', 'ecosia', 'brave', 'searx', 'mojeek', 'all'], help='API to use for search')
    parser.add_argument('--filetype', help='File type to filter results')
    parser.add_argument('--limit', type=int, default=10, help='Number of results to return')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds')
    parser.add_argument('--user-agent', help='Custom User-Agent string or path to a file containing it')
    parser.add_argument('--no-verify', action='store_true', help='Disable SSL verification')
    parser.add_argument('--output', default='results.csv', help='Output CSV file for results')
    parser.add_argument('--delay', type=int, default=0, help='Delay between requests in seconds')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--user-agent-file', help='Path to a file containing User-Agent strings')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    # Clear the terminal
    subprocess.run('clear' if sys.platform != 'win32' else 'cls', shell=True)

    # Load user-agent from file if specified
    user_agent = None
    if args.user_agent:
        try:
            if os.path.isfile(args.user_agent):
                with open(args.user_agent, 'r') as file:
                    user_agent = file.readline().strip()
            else:
                user_agent = args.user_agent
        except Exception as e:
            print(f"Error reading user-agent file: {e}")

    # Load user-agent from user-agent file if specified
    if args.user_agent_file:
        try:
            if os.path.isfile(args.user_agent_file):
                with open(args.user_agent_file, 'r') as file:
                    user_agent = file.readline().strip()
            else:
                print(f"User-Agent file '{args.user_agent_file}' not found.")
        except Exception as e:
            print(f"Error reading user-agent file: {e}")

    # API keys for different search engines
    api_keys = {
        'bing': 'YOUR_BING_API_KEY',
        'yandex': 'YOUR_YANDEX_API_KEY',
        'yahoo': 'YOUR_YAHOO_API_KEY',
        # Add other API keys here as needed
    }

    results = []
    engines_to_search = args.api if 'all' not in args.api else ['bing', 'google', 'duckduckgo', 'yandex', 'yahoo', 'ecosia', 'brave', 'searx', 'mojeek']

    for engine in engines_to_search:
        try:
            if engine == 'bing':
                search_results = search_bing(api_keys.get(engine), args.query, args.filetype, args.limit, args.timeout, user_agent, not args.no_verify)
            elif engine == 'google':
                search_results = search_google(args.query, args.filetype, args.limit, args.timeout, user_agent, not args.no_verify)
            elif engine == 'duckduckgo':
                search_results = search_duckduckgo(args.query, args.filetype, args.limit, args.timeout, user_agent, not args.no_verify)
            elif engine == 'yandex':
                search_results = search_yandex(api_keys.get(engine), args.query, args.filetype, args.limit, args.timeout, user_agent, not args.no_verify)
            elif engine == 'yahoo':
                search_results = search_yahoo(api_keys.get(engine), args.query, args.filetype, args.limit, args.timeout, user_agent, not args.no_verify)
            elif engine == 'ecosia':
                search_results = search_ecosia(args.query, args.filetype, args.limit, args.timeout, user_agent, not args.no_verify)
            elif engine == 'brave':
                search_results = search_brave(args.query, args.filetype, args.limit, args.timeout, user_agent, not args.no_verify)
            elif engine == 'searx':
                search_results = search_searx(args.query, args.filetype, args.limit, args.timeout, user_agent, not args.no_verify)
            elif engine == 'mojeek':
                search_results = search_mojeek(args.query, args.filetype, args.limit, args.timeout, user_agent, not args.no_verify)

            results.extend(search_results)

            if args.verbose:
                print(f"Found {len(search_results)} results from {engine}")

        except Exception as e:
            print(f"Failed to search {engine}: {e}")

        time.sleep(args.delay)

    save_results(results, args.output)

    if args.debug:
        print(f"Debug Info: Collected {len(results)} total results.")

if __name__ == "__main__":
    main()
