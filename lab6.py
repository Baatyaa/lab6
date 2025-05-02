import requests
import json
import logging
from datetime import datetime
import os


class AtaixOrderManager:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.ataix.kz/api"
        self.session = requests.Session()
        self.session.headers.update({
            "accept": "application/json",
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        })

        # Логирование қосу
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='ataix_orders.log'
        )

        # JSON файлдары үшін бума құру
        os.makedirs("adjusted_orders", exist_ok=True)

    def _make_request(self, method, endpoint, payload=None):
        """API сұрауын жасау"""
        try:
            response = self.session.request(
                method,
                f"{self.base_url}{endpoint}",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"API қатесі: {str(e)}")
            return {"status": False, "error": str(e)}

    def get_order_details(self, order_id):
        """Ордер туралы толық ақпарат алу"""
        return self._make_request("GET", f"/orders/{order_id}")

    def create_adjusted_order(self, original_order_id):
        """
        1% жоғары бағамен жаңа ордер құру және сақтау
        Параметрлер:
        - original_order_id: 1% жоғары құру үшін негізгі ордер ID
        """
        # 1. Түпнұсқа ордер ақпаратын алу
        original_order = self.get_order_details(original_order_id)
        if not original_order.get('status'):
            return original_order

        order_data = original_order['result']

        # 2. Жаңа бағаны есептеу (1% жоғары)
        old_price = float(order_data['price'])
        new_price = round(old_price * 1.01, 6)

        # 3. Жаңа ордер құру
        new_order = self._make_request("POST", "/orders", {
            "symbol": order_data['symbol'].replace("/", "/"),
            "side": order_data['side'],
            "type": "limit",
            "quantity": order_data['quantity'],
            "price": str(new_price),
            "subType": "gtc"
        })

        # 4. 1% жоғары ордерді сақтау
        if new_order.get('status'):
            filename = self._save_adjusted_order(original_order_id, order_data, new_order)
            return {
                "success": True,
                "message": "1% жоғары ордер сәтті құрылды және сақталды",
                "new_order_id": new_order['result']['orderID'],
                "old_price": old_price,
                "new_price": new_price,
                "file_path": filename
            }
        return new_order

    def _save_adjusted_order(self, original_id, original_data, new_order_data):
        """1% жоғары ордерді JSON файлға сақтау"""
        filename = f"adjusted_orders/1percent_higher_{original_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        data_to_save = {
            "original_order": {
                "id": original_id,
                "price": original_data['price'],
                "symbol": original_data['symbol'],
                "side": original_data['side']
            },
            "adjusted_order": {
                "id": new_order_data['result']['orderID'],
                "price": new_order_data['result']['price'],
                "created_at": datetime.now().isoformat()
            },
            "price_increase": {
                "percentage": "1%",
                "old_price": float(original_data['price']),
                "new_price": float(new_order_data['result']['price'])
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)

        logging.info(f"1% жоғары ордер сақталды: {filename}")
        return filename

    def list_adjusted_orders(self):
        """Сақталған 1% жоғары ордерлер тізімін шығару"""
        files = []
        for file in os.listdir("adjusted_orders"):
            if file.startswith("1percent_higher_"):
                files.append({
                    "filename": file,
                    "path": os.path.join("adjusted_orders", file)
                })
        return files


# Мысал қолдану
if __name__ == "__main__":
    # Конфигурация
    API_KEY = "wHxKGrbUdTRvHLT4Ldjho0PpOCqFEc6bW8tWstnSLAfJi0uu7aZFJWlhzkp2Un43zmgrTp0pVQskg7GKFHJJ4n"  # Нақты API кілтіңізді қойыңыз
    ORDER_ID = "LTC-USDT-33994-1746196335868"  # Негізгі ордер ID

    # Менеджерді іске қосу
    manager = AtaixOrderManager(API_KEY)

    # 1% жоғары ордер құру және сақтау
    result = manager.create_adjusted_order(ORDER_ID)

    # Нәтижені көрсету
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Сақталған ордерлер тізімі
    print("\nСақталған ордерлер:")
    print(json.dumps(manager.list_adjusted_orders(), indent=2))