from django import forms
from .models import ProductImage

class ProductImageForm(forms.ModelForm):
    """商品圖片上傳表單"""
    
    class Meta:
        model = ProductImage
        fields = ['image']
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'multiple': False
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].label = '選擇農產品圖片'
        self.fields['image'].help_text = '支援 JPG、PNG、GIF 等圖片格式'

class StoryGenerationForm(forms.Form):
    """故事生成表單"""
    
    STORY_STYLES = [
        ('温馨家庭', '溫馨家庭風格'),
        ('田園詩意', '田園詩意風格'), 
        ('健康養生', '健康養生風格'),
        ('懷舊復古', '懷舊復古風格'),
        ('現代簡約', '現代簡約風格'),
        ('兒童友好', '兒童友好風格'),
        ('專業科普', '專業科普風格'),
        ('浪漫情懷', '浪漫情懷風格'),
    ]
    
    story_prompt = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '請描述您想要的故事內容，例如：「講述這個農產品從種植到餐桌的溫馨故事」或「介紹這個產品的營養價值和健康功效」'
        }),
        label='故事描述',
        help_text='請簡潔描述您想要生成什麼樣的產品故事（最多500字）'
    )
    
    story_style = forms.ChoiceField(
        choices=STORY_STYLES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='故事風格',
        help_text='選擇您偏好的故事風格'
    )