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
    
    def generate_product_story(self, product_info, story_prompt, story_style):
        """根據產品資訊和使用者指令生成產品故事"""
        try:
            # 根據風格調整提示詞
            style_prompts = {
                '温馨家庭': '請以溫馨、親切的家庭視角，強調產品與家人情感連結的故事',
                '田園詩意': '請以優美的田園詩意風格，描述產品與大自然和諧共生的故事', 
                '健康養生': '請以專業又親和的語調，重點介紹產品的營養價值和健康益處',
                '懷舊復古': '請以懷舊的語調，訴說產品承載的傳統文化和歷史記憶',
                '現代簡約': '請以簡潔明快的現代風格，突出產品的品質和特色',
                '兒童友好': '請以活潑有趣的語言，適合向兒童介紹這個產品',
                '專業科普': '請以專業的科普語調，詳細介紹產品的特性和知識',
                '浪漫情懷': '請以浪漫詩意的語言，描述產品帶來的美好體驗'
            }
            
            style_instruction = style_prompts.get(story_style, '請以友善親切的語調')
            
            prompt = f"""
            根據以下農產品資訊，{style_instruction}，生成一個引人入勝的產品故事。

            產品資訊：
            - 產品名稱：{product_info.get('product_name', '未知產品')}
            - 產品描述：{product_info.get('description', '無描述')}
            - 產品類別：{product_info.get('category', '未知類別')}
            - 產品特色：{', '.join(product_info.get('features', []))}
            - 目標客群：{product_info.get('target_audience', '未知')}

            使用者故事需求：{story_prompt}

            故事風格：{story_style}

            請生成一個約200-400字的產品故事，要求：
            1. 內容必須真實可信，不可誇大不實
            2. 語言生動有趣，富有感情色彩
            3. 突出產品的特色和價值
            4. 符合選定的風格調性
            5. 適合用於產品行銷和介紹
            6. 使用繁體中文
            
            請直接回傳故事內容，不需要額外的格式標記。
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=600,
                temperature=0.7
            )
            
            story_content = response.choices[0].message.content.strip()
            return story_content
            
        except Exception as e:
            return f"故事生成失敗：{str(e)}"