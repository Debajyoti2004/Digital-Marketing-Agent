import requests
import json
import config

class AmazonAPI:
    SP_API_URL = "https://sellingpartnerapi-na.amazon.com"
    LWA_URL = "https://api.amazon.com/auth/o2/token"

    def _get_access_token(self):
        p = {
            "grant_type": "refresh_token",
            "refresh_token": config.AMAZON_SP_API_REFRESH_TOKEN,
            "client_id": config.AMAZON_SP_API_CLIENT_ID,
            "client_secret": config.AMAZON_SP_API_CLIENT_SECRET
        }
        r = requests.post(self.LWA_URL, data=p)
        r.raise_for_status()
        return r.json()["access_token"]

    def _request(self, method, endpoint, params=None, data=None, json_data=None, headers=None, files=None):
        h = headers or {"x-amz-access-token": self._get_access_token(), "Content-Type": "application/json"}
        if "x-amz-access-token" not in h:
            h["x-amz-access-token"] = self._get_access_token()
        r = requests.request(method, f"{self.SP_API_URL}{endpoint}", headers=h, params=params, data=data, json=json_data, files=files, timeout=30)
        r.raise_for_status()
        return r.json()

    def create_or_update_listing(self, sku, product_title, description, bullet_points, price, keywords):
        d = {
            "productType": "PRODUCT",
            "patches": [
                {"op": "replace", "path": "/attributes/item_name", "value": [{"value": product_title, "language_tag": "en_IN"}]},
                {"op": "replace", "path": "/attributes/product_description", "value": [{"value": description, "language_tag": "en_IN"}]},
                {"op": "replace", "path": "/attributes/bullet_point", "value": [{"value": bp, "language_tag": "en_IN"} for bp in bullet_points]},
                {"op": "replace", "path": "/attributes/generic_keywords", "value": [{"value": kw, "language_tag": "en_IN"} for kw in keywords]},
                {"op": "replace", "path": "/attributes/purchasable_offer", "value": [{"marketplace_id": config.AMAZON_MARKETPLACE_ID, "our_price": [{"schedule": [{"value_with_tax": price}]}]}]}
            ]
        }
        e = f"/listings/2021-08-01/items/{config.AMAZON_SELLER_ID}/{sku}"
        return self._request("PATCH", e, params={"marketplaceIds": config.AMAZON_MARKETPLACE_ID}, json_data=d)

    def get_listing(self, sku):
        e = f"/listings/2021-08-01/items/{config.AMAZON_SELLER_ID}/{sku}"
        return self._request("GET", e, params={"marketplaceIds": config.AMAZON_MARKETPLACE_ID})

    def update_price(self, sku, price):
        d = {"sku": sku, "prices": [{"marketplaceId": config.AMAZON_MARKETPLACE_ID, "listingPrice": {"currencyCode": "USD", "amount": price}}]}
        e = "/products/pricing/v0/price"
        return self._request("PUT", e, json_data=d)

    def update_inventory(self, sku, quantity):
        d = {"sku": sku, "marketplaceId": config.AMAZON_MARKETPLACE_ID, "fulfillmentAvailability": [{"quantity": quantity}]}
        e = f"/listings/2021-08-01/items/{config.AMAZON_SELLER_ID}/{sku}"
        return self._request("PATCH", e, json_data=d)

    def upload_product_image(self, sku, file_path):
        e = f"/listings/2021-08-01/items/{config.AMAZON_SELLER_ID}/{sku}/images"
        upload_req = {
            "sku": sku,
            "marketplaceId": config.AMAZON_MARKETPLACE_ID,
            "images": [{"imageType": "MAIN"}]
        }
        upload_info = self._request("POST", e, json_data=upload_req)
        if "uploadUrl" in upload_info:
            upload_url = upload_info["uploadUrl"]
            with open(file_path, "rb") as f:
                headers = {"Content-Type": "image/jpeg"}
                resp = requests.put(upload_url, headers=headers, data=f)
                resp.raise_for_status()
            return {"status": "success", "message": f"Image uploaded for SKU {sku}"}
        return {"status": "error", "message": "No upload URL returned from Amazon"}

    def get_orders(self, created_after=None, order_statuses=None):
        p = {"MarketplaceIds": config.AMAZON_MARKETPLACE_ID}
        if created_after:
            p["CreatedAfter"] = created_after
        if order_statuses:
            p["OrderStatuses"] = ",".join(order_statuses)
        e = "/orders/v0/orders"
        return self._request("GET", e, params=p)

    def confirm_shipment(self, order_id, tracking_number, carrier_code):
        d = {"orderId": order_id, "trackingNumber": tracking_number, "carrierCode": carrier_code}
        e = f"/orders/v0/orders/{order_id}/shipmentConfirmation"
        return self._request("POST", e, json_data=d)

    def cancel_order(self, order_id, reason="CustomerRequested"):
        d = {"reason": reason}
        e = f"/orders/v0/orders/{order_id}/cancel"
        return self._request("POST", e, json_data=d)

    def request_report(self, report_type, start_date=None, end_date=None):
        d = {"reportType": report_type, "marketplaceIds": [config.AMAZON_MARKETPLACE_ID]}
        if start_date:
            d["dataStartTime"] = start_date
        if end_date:
            d["dataEndTime"] = end_date
        e = "/reports/2021-06-30/reports"
        return self._request("POST", e, json_data=d)

    def get_report_document(self, report_document_id):
        e = f"/reports/2021-06-30/documents/{report_document_id}"
        return self._request("GET", e)

    def download_report(self, url):
        r = requests.get(url)
        r.raise_for_status()
        return r.content
