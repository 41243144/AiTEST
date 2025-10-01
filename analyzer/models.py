from django.db import models
import uuid
import os

def upload_to(instance, filename):
    """產生上傳檔案路徑"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('uploads', filename)

class ProductImage(models.Model):
    """商品圖片模型"""
    image = models.ImageField(upload_to=upload_to, verbose_name='商品圖片')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='上傳時間')
    
    # AI 分析結果
    product_name = models.CharField(max_length=200, blank=True, verbose_name='商品名稱')
    description = models.TextField(blank=True, verbose_name='商品介紹')
    recommended_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name='推薦售價'
    )
    analysis_json = models.JSONField(null=True, blank=True, verbose_name='完整分析結果')
    analyzed = models.BooleanField(default=False, verbose_name='已分析')
    
    # 故事生成相關欄位
    story_content = models.TextField(blank=True, verbose_name='產品故事')
    story_style = models.CharField(max_length=50, blank=True, verbose_name='故事風格')
    story_prompt = models.TextField(blank=True, verbose_name='使用者故事指令')
    story_generated = models.BooleanField(default=False, verbose_name='已生成故事')
    
    class Meta:
        verbose_name = '商品圖片'
        verbose_name_plural = '商品圖片'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"商品圖片 - {self.product_name or '未分析'}"
