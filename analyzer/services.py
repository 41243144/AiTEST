import openai
import json
import base64
from django.conf import settings
from PIL import Image
import io

class OpenAIService:
    """OpenAI API 服務類別"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def encode_image(self, image_path):
        """將圖片編碼為 base64"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise Exception(f"圖片編碼失敗: {str(e)}")
    
    def analyze_product_image(self, image_path):
        """分析商品圖片並回傳 JSON 格式結果"""
        try:
            # 編碼圖片
            base64_image = self.encode_image(image_path)
            
            # 準備提示詞
            prompt = """
                請仔細分析這張圖片中的商品，並以 JSON 格式回傳以下資訊。
                即使是原始農產品、食材或物品，也請盡量給出具體的商品名稱和詳細資訊：
                
                {
                    "product_name": "商品名稱（繁體中文，必填）",
                    "description": "詳細的商品介紹（繁體中文，包含特色、用途、材質等）",
                    "recommended_price": 100,
                    "category": "商品類別",
                    "features": ["特色1", "特色2", "特色3"],
                    "target_audience": "目標客群",
                    "usage_scenarios": ["使用場景1", "使用場景2"]
                }
                
                分析指引：
                - 如果是蔬菜水果，請標明具體品種（如：牛番茄、小番茄、青椒等）
                - 如果是食材，請描述其營養價值和烹飪用途
                - 如果是包裝商品，請描述包裝特色和品牌資訊
                - 價格請根據台灣市場行情估算（recommended_price 必須是純數字）
                - 如果真的無法識別，才在 product_name 中填入 "無法識別的商品"
                
                重要規則：
                1. recommended_price 必須是純數字（不要包含貨幣符號、文字或其他字符）
                2. 如果無法估算價格，請填入 0
                3. 價格單位為新台幣
                4. 請務必以繁體中文回答其他欄位
                5. 確保回傳的是有效的 JSON 格式
                """
            
            # 發送請求到 OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o",  # 使用支援視覺的模型
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=800,
                temperature=0.1
            )
            
            # 解析回應
            content = response.choices[0].message.content

            
            # 嘗試解析 JSON
            try:
                # 移除可能的 markdown 代碼塊標記
                if content.startswith('```json'):
                    content = content[7:]
                if content.endswith('```'):
                    content = content[:-3]
                
                result = json.loads(content.strip())
                print("解析結果:", result)
                
                # 處理推薦售價，確保是數字格式
                if 'recommended_price' in result:
                    price_value = result['recommended_price']
                    try:
                        # 如果是字串，嘗試提取數字
                        if isinstance(price_value, str):
                            # 移除所有非數字字符（除了小數點）
                            import re
                            price_str = re.sub(r'[^\d.]', '', price_value)
                            if price_str:
                                result['recommended_price'] = float(price_str)
                            else:
                                result['recommended_price'] = 0
                        elif isinstance(price_value, (int, float)):
                            result['recommended_price'] = float(price_value)
                        else:
                            result['recommended_price'] = 0
                    except (ValueError, TypeError):
                        result['recommended_price'] = 0
                else:
                    result['recommended_price'] = 0
                
                return result
                
            except json.JSONDecodeError as e:
                # 如果 JSON 解析失敗，回傳基本格式
                return {
                    "product_name": "分析失敗",
                    "description": f"OpenAI 回應解析失敗: {str(e)}",
                    "recommended_price": 0,
                    "category": "未知",
                    "features": [],
                    "target_audience": "未知",
                    "usage_scenarios": [],
                    "raw_response": content
                }
                
        except Exception as e:
            return {
                "product_name": "分析錯誤",
                "description": f"分析過程發生錯誤: {str(e)}",
                "recommended_price": 0,
                "category": "錯誤",
                "features": [],
                "target_audience": "未知", 
                "usage_scenarios": [],
                "error": str(e)
            }