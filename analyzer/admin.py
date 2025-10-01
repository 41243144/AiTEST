from django.contrib import admin
from .models import ProductImage

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'recommended_price', 'analyzed', 'story_generated', 'uploaded_at')
    list_filter = ('analyzed', 'story_generated', 'story_style', 'uploaded_at')
    search_fields = ('product_name', 'description', 'story_content')
    readonly_fields = ('uploaded_at', 'analysis_json')
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('image', 'uploaded_at')
        }),
        ('分析結果', {
            'fields': ('product_name', 'description', 'recommended_price', 'analyzed')
        }),
        ('故事生成', {
            'fields': ('story_prompt', 'story_style', 'story_content', 'story_generated')
        }),
        ('詳細資料', {
            'fields': ('analysis_json',),
            'classes': ('collapse',)
        })
    )
