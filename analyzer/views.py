from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import os

from .models import ProductImage
from .forms import ProductImageForm
from .services import OpenAIService

def index(request):
    """首頁視圖"""
    recent_images = ProductImage.objects.all()[:10]
    return render(request, 'analyzer/index.html', {
        'recent_images': recent_images
    })

def upload_image(request):
    """上傳圖片視圖"""
    if request.method == 'POST':
        form = ProductImageForm(request.POST, request.FILES)
        if form.is_valid():
            # 儲存圖片
            product_image = form.save()
            
            # 分析圖片
            try:
                openai_service = OpenAIService()
                image_path = product_image.image.path
                analysis_result = openai_service.analyze_product_image(image_path)
                
                # 更新模型資料
                product_image.product_name = analysis_result.get('product_name', '')
                product_image.description = analysis_result.get('description', '')
                
                # 安全處理價格
                try:
                    price = analysis_result.get('recommended_price', 0)
                    if isinstance(price, str):
                        import re
                        price_str = re.sub(r'[^\d.]', '', price)
                        product_image.recommended_price = float(price_str) if price_str else 0
                    else:
                        product_image.recommended_price = float(price) if price else 0
                except (ValueError, TypeError):
                    product_image.recommended_price = 0
                
                product_image.analysis_json = analysis_result
                product_image.analyzed = True
                product_image.save()
                
                messages.success(request, '圖片上傳並分析成功！')
                return redirect('analyzer:result', pk=product_image.pk)
                
            except Exception as e:
                messages.error(request, f'圖片分析失敗: {str(e)}')
                return redirect('analyzer:upload')
        else:
            messages.error(request, '圖片上傳失敗，請檢查檔案格式。')
    else:
        form = ProductImageForm()
    
    return render(request, 'analyzer/upload.html', {'form': form})

def result(request, pk):
    """結果顯示視圖"""
    product_image = get_object_or_404(ProductImage, pk=pk)
    return render(request, 'analyzer/result.html', {
        'product_image': product_image
    })

def history(request):
    """歷史記錄視圖"""
    images = ProductImage.objects.all()
    return render(request, 'analyzer/history.html', {
        'images': images
    })

@csrf_exempt
@require_http_methods(["POST"])
def api_analyze(request):
    """API 端點：分析圖片"""
    try:
        if 'image' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': '沒有上傳圖片'
            }, status=400)
        
        # 建立 ProductImage 實例
        form = ProductImageForm(request.POST, request.FILES)
        if form.is_valid():
            product_image = form.save()
            
            # 分析圖片
            openai_service = OpenAIService()
            image_path = product_image.image.path
            analysis_result = openai_service.analyze_product_image(image_path)
            
            # 更新模型資料
            product_image.product_name = analysis_result.get('product_name', '')
            product_image.description = analysis_result.get('description', '')
            
            # 安全處理價格
            try:
                price = analysis_result.get('recommended_price', 0)
                if isinstance(price, str):
                    import re
                    price_str = re.sub(r'[^\d.]', '', price)
                    product_image.recommended_price = float(price_str) if price_str else 0
                else:
                    product_image.recommended_price = float(price) if price else 0
            except (ValueError, TypeError):
                product_image.recommended_price = 0
                
            product_image.analysis_json = analysis_result
            product_image.analyzed = True
            product_image.save()
            
            return JsonResponse({
                'success': True,
                'data': {
                    'id': product_image.pk,
                    'product_name': product_image.product_name,
                    'description': product_image.description,
                    'recommended_price': float(product_image.recommended_price) if product_image.recommended_price else 0,
                    'analysis': analysis_result
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': '表單驗證失敗',
                'form_errors': form.errors
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'分析失敗: {str(e)}'
        }, status=500)
