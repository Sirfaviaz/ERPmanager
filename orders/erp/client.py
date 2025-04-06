from django.conf import settings
import requests
import json  


class ERPClient:
    def __init__(self):
        self.base_url = settings.ERP_BASE_URL
        self.api_key = settings.ERP_API_KEY
        self.api_secret = settings.ERP_API_SECRET

    def _headers(self):
        return {
            "Authorization": f"token {self.api_key}:{self.api_secret}",
            "Content-Type": "application/json"
        }

  
    def search_items(self, query):
        try:
            url = f"{self.base_url}/api/method/frappe.desk.search.search_link"
            params = {
                "doctype": "Item",
                "txt": query,
                "limit_page_length": 20
            }
            response = requests.get(url, headers=self._headers(), params=params)

            print("ERP Response Status:", response.status_code)
            print("ERP Response Text:", response.text)

            response.raise_for_status()

            # Extract from message instead of data
            raw_results = response.json().get("message", [])
            return [
                {
                    "item_code": item["value"],
                    "item_name": item["description"].split(",")[0]  # Clean up extra HTML/text
                }
                for item in raw_results
            ]
        except Exception as e:
            print("ERP Item Search Error:", str(e))
            return []

    def get_item_stock(self, item_code):
        """
        Fetches stock from all warehouses for a given item.
        Returns a list of dicts with warehouse, qty, valuation_rate.
        """
        try:
            url = f"{self.base_url}/api/method/frappe.client.get_list"
            params = {
                "doctype": "Bin",
                "fields": json.dumps(["warehouse", "actual_qty", "valuation_rate"]),
                "filters": json.dumps([["item_code", "=", item_code]])
            }
            response = requests.get(url, headers=self._headers(), params=params)
            response.raise_for_status()
            return response.json().get("message", [])  # list of stock per warehouse
        except Exception as e:
            print("ERP Stock Fetch Error:", str(e))
            return []

