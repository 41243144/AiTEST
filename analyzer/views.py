from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import os

from .models import ProductImage
from .forms import ProductImageForm, StoryGenerationForm
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
    story_form = StoryGenerationForm()
    
    return render(request, 'analyzer/result.html', {
        'product_image': product_image,
        'story_form': story_form
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

def generate_story(request, pk):
    """生成產品故事視圖"""
    product_image = get_object_or_404(ProductImage, pk=pk)
    
    if request.method == 'POST':
        form = StoryGenerationForm(request.POST)
        if form.is_valid():
            story_prompt = form.cleaned_data['story_prompt']
            story_style = form.cleaned_data['story_style']
            
            try:
                # 確保產品已經分析過
                if not product_image.analyzed or not product_image.analysis_json:
                    messages.error(request, '請先完成產品分析後再生成故事。')
                    return redirect('analyzer:result', pk=pk)
                
                # 生成故事
                openai_service = OpenAIService()
                story_content = openai_service.generate_product_story(
                    product_image.analysis_json,
                    story_prompt,
                    story_style
                )
                
                # 更新產品資訊
                product_image.story_content = story_content
                product_image.story_style = story_style
                product_image.story_prompt = story_prompt
                product_image.story_generated = True
                product_image.save()
                
                messages.success(request, '產品故事生成成功！')
                return redirect('analyzer:result', pk=pk)
                
            except Exception as e:
                messages.error(request, f'故事生成失敗: {str(e)}')
                return redirect('analyzer:result', pk=pk)
        else:
            messages.error(request, '表單填寫有誤，請檢查後重新提交。')
    
    return redirect('analyzer:result', pk=pk)

@csrf_exempt
@require_http_methods(["POST"])
def api_generate_story(request):
    """API 端點：生成產品故事"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        story_prompt = data.get('story_prompt')
        story_style = data.get('story_style')
        
        if not all([product_id, story_prompt, story_style]):
            return JsonResponse({
                'success': False,
                'error': '缺少必要參數：product_id, story_prompt, story_style'
            }, status=400)
        
        product_image = get_object_or_404(ProductImage, pk=product_id)
        
        if not product_image.analyzed or not product_image.analysis_json:
            return JsonResponse({
                'success': False,
                'error': '產品尚未分析完成'
            }, status=400)
        
        # 生成故事
        openai_service = OpenAIService()
        story_content = openai_service.generate_product_story(
            product_image.analysis_json,
            story_prompt,
            story_style
        )
        
        # 更新產品資訊
        product_image.story_content = story_content
        product_image.story_style = story_style
        product_image.story_prompt = story_prompt
        product_image.story_generated = True
        product_image.save()
        
        return JsonResponse({
            'success': True,
            'data': {
                'story_content': story_content,
                'story_style': story_style,
                'story_prompt': story_prompt
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'故事生成失敗: {str(e)}'
        }, status=500)